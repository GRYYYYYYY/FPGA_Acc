"""Reauthenticate each completed paired run, live estimator output and pressure payload."""
import argparse,json,re,shutil
from pathlib import Path
from prepared_csr import read
from pre_route_endpoints import sha


def main():
    parser=argparse.ArgumentParser();parser.add_argument('design');args=parser.parse_args();base=Path('experiments');design=args.design
    if design=='adder_tree_2L_032bits':
        trial=base/'native_pressure_paired_cached_cost_2026-10-06';work=Path('work/native_pressure_paired_cached_cost_2026-10-06')
    else:
        trial=base/'native_pressure_paired_cached_cohort_2026-10-06'/design;work=Path('work/native_pressure_paired_cached_cohort_2026-10-06')/design
    r=json.loads((trial/'receipt.json').read_text());p=json.loads((trial/'protocol.json').read_text());assert sha(trial/'protocol.json')==r['protocol_sha256']
    assert [row['mode'] for row in r['results']]==p['sequence']==['off','on','on','off']*2
    assert all(sha(v['path'])==v['sha256'] for v in p['inputs'].values()) and all(sha(trial/'source'/n)==h for n,h in p['sources'].items())
    prepared=base/'adder_tree_family_length_switch_csr_2026-10-06'/design;prep=json.loads((prepared/'receipt.json').read_text());assert sha(prepared/'receipt.json')==p['csr_receipt_sha256'] and sha(prepared/'csr/manifest.json')==prep['manifest_sha256']
    baseline=base/'adder_tree_family_predictions_2026-10-06'/design/'sparse_reset';br=json.loads((baseline/'receipt.json').read_text());assert sha(baseline/'receipt.json')==p['baseline_receipt_sha256'] and sha(baseline/'prediction.json')==br['prediction_sha256']
    m,f=read(prepared/'csr',p['inputs']['rr_graph']['sha256']);occ=json.loads((baseline/'prediction.json').read_text())['node_occupancy']
    rows=[(n,f['capacities'][n],1+max(0,occ.get(str(n),0)-f['capacities'][n])/f['capacities'][n]) for n in range(m['nodes']) if f['types'][n] in (4,5) and f['capacities'][n]>0 and occ.get(str(n),0)>f['capacities'][n]]
    expected=f"ROUTECAST_PRESSURE_V1 {m['nodes']} {p['inputs']['rr_graph']['sha256']}\n"+''.join(f'{n} {cap} {v:.9g}\n' for n,cap,v in rows)
    bindings={str(trial/'receipt.json'):sha(trial/'receipt.json')};cycles=[]
    for row in r['results']:
        i=row['run'];mode=row['mode'];tag=f'{i:02d}_{mode}';route=work/tag/'design.route';log=trial/(tag+'.log')
        assert sha(route)==row['route_sha256'] and sha(log)==row['log_sha256'];text=log.read_text();assert 'VPR succeeded' in text and 'Completed routing consistency check successfully' in text
        assert float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',text)[1])==row['cpd_ns']
        assert int(re.search(r'Total wirelength:\s*(\d+)',text)[1])==row['wirelength']
        assert row['cached_pipeline_s']+1e-8>=row['estimator_s']+row['payload_s']+row['native_route_s']
        bindings[str(route)]=sha(route);bindings[str(log)]=sha(log)
        if mode=='on':
            payload=trial/(tag+'.pressure');assert payload.read_text()==expected and row['pressure_nodes']==len(rows)
            pred=trial/(tag+'_prediction');pr=json.loads((pred/'receipt.json').read_text());pp=json.loads((pred/'protocol.json').read_text())
            assert sha(pred/'protocol.json')==pr['protocol_sha256'] and sha(pred/'prediction.json')==pr['prediction_sha256']==br['prediction_sha256']
            assert sha(pred/'net_results.jsonl')==pr['journal_sha256'] and sha(pred/'consumer')==pp['binary_sha256'] and pr['failed']==0
            assert pp['inputs']['graph']==p['inputs']['rr_graph'] and pp['csr_manifest_sha256']==prep['manifest_sha256']
            assert row['estimator_s']>=pr['full_prediction_wall_s']
            assert f'RouteCast pressure applied: {len(rows)} channel nodes' in text
            for path in (payload,pred/'receipt.json',pred/'protocol.json',pred/'prediction.json'):bindings[str(path)]=sha(path)
        else:assert row['estimator_s']==row['payload_s']==row['pressure_nodes']==0 and 'RouteCast pressure applied' not in text
    for mode in ('off','on'):
        group=[row for row in r['results'] if row['mode']==mode]
        assert len({row['route_sha256'] for row in group})==1
        assert sum(row['cached_pipeline_s'] for row in group)/len(group)==r['mean_cached_pipeline_s'][mode]
    for cycle in (0,1):
        group=r['results'][cycle*4:(cycle+1)*4];means={mode:sum(v['cached_pipeline_s'] for v in group if v['mode']==mode)/2 for mode in ('off','on')}
        cycles.append({'cycle':cycle,'mean_cached_pipeline_s':means,'off_over_on':means['off']/means['on']})
    assert all(sha(path)==h for path,h in bindings.items())
    out=base/'native_pressure_paired_evidence_verification_2026-10-06'/design;out.mkdir(parents=True);shutil.copyfile(__file__,out/'source.py')
    report={'trial_receipt_sha256':sha(trial/'receipt.json'),'source_sha256':sha(__file__),'input_sha256':bindings,'all_evidence_checks_pass':True,'pressure_rows':len(rows),'cycles':cycles,'scope':'same cached-pipeline/one-design ABBA evidence; no cold/unseen-family/hardware net gain claim'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'all_evidence_checks_pass':True},indent=2)+'\n');print(json.dumps({'design':design,'pressure_rows':len(rows),'cycles':cycles}),flush=True)


if __name__=='__main__':main()
