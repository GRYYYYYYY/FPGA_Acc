"""Complete fixed four-case comparison with independent path and evidence checks."""
import json
import shutil
from pathlib import Path
from pre_route_endpoints import sha


def load_receipt(root):
    receipt=json.loads((root/'receipt.json').read_text())
    if 'protocol_sha256' in receipt:
        assert sha(root/'protocol.json')==receipt['protocol_sha256']
    return receipt


def main():
    base=Path('experiments');capture=base/'adder_tree_family_native_capture_v2_2026-10-06'
    cp=json.loads((capture/'protocol.json').read_text());cr=load_receipt(capture)
    assert cr['all_exit_zero']
    expected=[f'adder_tree_{depth}L_{width:03d}bits' for depth in (2,3) for width in (32,128)]
    assert cp['cohort']==expected
    lineage=base/'adder_tree_family_lineage_2026-10-06/receipt.json'
    lr=json.loads(lineage.read_text());assert lr['all_54_variants_regenerate_byte_exact']
    records=[];bindings={str(lineage):sha(lineage),str(capture/'receipt.json'):sha(capture/'receipt.json')}
    for design in expected:
        models={};predictions={};protocols={}
        for model in ('sparse_reset','bbox3'):
            root=base/'adder_tree_family_predictions_2026-10-06'/design/model
            physical=Path(str(root)+'_physical_audit');evaluation=base/'adder_tree_family_evaluation_2026-10-06'/design/model
            r=load_receipt(root);ar=load_receipt(physical);er=load_receipt(evaluation)
            p=json.loads((root/'protocol.json').read_text());ap=json.loads((physical/'protocol.json').read_text());ep=json.loads((evaluation/'protocol.json').read_text())
            assert sha(root/'prediction.json')==r['prediction_sha256'] and sha(root/'net_results.jsonl')==r['journal_sha256']
            assert sha(root/'consumer')==p['binary_sha256']
            assert all(sha(path)==h for path,h in p['source_sha256'].items())
            assert all(sha(physical/'source'/name)==h for name,h in ap['source_sha256'].items())
            assert all(sha(evaluation/'source'/name)==h for name,h in ep['source_sha256'].items())
            assert ar['prediction_receipt_sha256']==sha(root/'receipt.json')
            assert ep['physical_audit_receipt_sha256']==sha(physical/'receipt.json')
            assert ar['result']['all_physical_and_union_checks_passed'] and er['exact_full_cohort_match']
            assert er['reports']['requested_connections']==r['connections']==ar['result']['requested']
            assert er['reports']['prediction_overflow_units']==ar['result']['all_type_overuse_units']
            assert er['reports']['native_overflow_units']==0
            assert sha(evaluation/'spatial_maps.json')==er['spatial_maps_sha256']
            for v in ep['inputs'].values():
                assert sha(v['path'])==v['sha256'];bindings[v['path']]=v['sha256']
            for directory in (root,physical,evaluation):
                for name in ('protocol.json','receipt.json'):bindings[str(directory/name)]=sha(directory/name)
            predictions[model]=json.loads((root/'prediction.json').read_text());protocols[model]=p
            models[model]={'metrics':er['reports'],'timing':{k:r[k] for k in ('full_prediction_wall_s','search_ledger_s','cold_conversion_wall_s')},'edge_visits':r['edge_visits'],'settled_nodes':r['settled_nodes'],'failed':r['failed']}
        a=predictions['sparse_reset'];b=predictions['bbox3'];pa=protocols['sparse_reset'];pb=protocols['bbox3']
        assert pa['inputs']==pb['inputs'] and pa['csr_manifest_sha256']==pb['csr_manifest_sha256']
        assert len(a['connections'])==len(b['connections'])
        changed=0
        for x,y in zip(a['connections'],b['connections']):
            assert all(x[k]==y[k] for k in ('connection_id','net_id','source','sink'))
            changed+=x['physical_edge_ids']!=y['physical_edge_ids']
        for metric in ('resource','spatial'):
            for key in ('universe_size','k','top_k_tie_rule','nonzero_truth','truth_k_boundary'):
                assert models['sparse_reset']['metrics'][metric][key]==models['bbox3']['metrics'][metric][key]
        records.append({'design':design,'connections':len(a['connections']),'changed_paths':changed,
                        'occupancy_equal':a['node_occupancy']==b['node_occupancy'],'models':models})
    assert sum(r['connections'] for r in records)==7936
    assert all(sha(path)==h for path,h in bindings.items())
    out=base/'adder_tree_family_model_comparison_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py')
    report={'cohort':expected,'total_connections':7936,'family_count':1,'records':records,'evidence_sha256':bindings,
            'source_sha256':sha(__file__),'unseen_family_claim':False,'repair_committed':False,
            'scope':'complete fixed four-case arithmetic readiness/transfer comparison, not four independent families',
            'timing_limitations':'concurrent development workloads, conversion separate, no matched end-to-end native feedback timing',
            'remaining_gates':['authenticated upstream provenance/whole-family unseen split','native feedback final QoR and total time benefit','hardware deployment gates']}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'complete_fixed_cohort':True,'connections':7936,'repair_committed':False},indent=2)+'\n')
    print(json.dumps({'connections':7936,'records':[{'design':r['design'],'changed_paths':r['changed_paths'],'overflow':[r['models'][m]['metrics']['prediction_overflow_units'] for m in ('sparse_reset','bbox3')]} for r in records]}),flush=True)


if __name__=='__main__':main()
