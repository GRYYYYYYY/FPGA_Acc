"""Independent original XML audit for representative byte-repeatable paired routes."""
import argparse,json,shutil,time
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit


def main():
    parser=argparse.ArgumentParser();parser.add_argument('design');args=parser.parse_args();base=Path('experiments')
    if args.design=='adder_tree_2L_032bits':
        trial=base/'native_pressure_paired_cached_cost_2026-10-06';work=Path('work/native_pressure_paired_cached_cost_2026-10-06')
    else:
        trial=base/'native_pressure_paired_cached_cohort_2026-10-06'/args.design;work=Path('work/native_pressure_paired_cached_cohort_2026-10-06')/args.design
    r=json.loads((trial/'receipt.json').read_text());p=json.loads((trial/'protocol.json').read_text());assert sha(trial/'protocol.json')==r['protocol_sha256'] and r['within_mode_route_byte_repeatable']
    front=base/'adder_tree_family_endpoints_2026-10-06'/args.design;fr=json.loads((front/'receipt.json').read_text());ep=front/'endpoints.json';assert sha(ep)==fr['outputs']['endpoints.json'];e=json.loads(ep.read_text());expected=Counter((v['net_id'],v['source'],v['sink']) for v in e['connections'])
    out=base/'native_pressure_paired_route_audit_2026-10-06'/args.design;out.mkdir(parents=True);(out/'source').mkdir()
    names=['audit_paired_pressure_routes.py','stream_native_route_audit.py','audit_native_route.py','pre_route_endpoints.py'];sources={n:sha(Path('tools')/n) for n in names}
    for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
    protocol={'trial_receipt_sha256':sha(trial/'receipt.json'),'inputs':p['inputs'],'sources':sources,'endpoints_sha256':sha(ep),'scope':'original XML printed arcs/switches/net-union/full endpoint-cohort of representative off/on routes; all within-mode byte repeats certified by paired trial'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[]
    for mode in ('off','on'):
        row=next(v for v in r['results'] if v['mode']==mode);tag=f'{row["run"]:02d}_{mode}';route=work/tag/'design.route';assert sha(route)==row['route_sha256'];start=time.monotonic()
        result=audit(p['inputs']['rr_graph']['path'],route);actual=Counter((v['net_id'],v['source'],v['sink']) for v in result['connections'])
        assert actual==expected and result['all_printed_branch_arc_switch_and_union_checks_pass'] and result['overflow_units']==0
        (out/(mode+'_physical_branches.json')).write_text(json.dumps(result)+'\n')
        results.append({'mode':mode,'connections':sum(actual.values()),'route_sha256':sha(route),'physical_branches_sha256':sha(out/(mode+'_physical_branches.json')),'overflow_units':0,'full_cohort_exact':True,'wall_s':time.monotonic()-start})
    assert all(sha(v['path'])==v['sha256'] for v in p['inputs'].values()) and all(sha(Path('tools')/n)==h for n,h in sources.items())
    (out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':results,'all_pass':True,'scope':protocol['scope']},indent=2)+'\n');print(json.dumps(results),flush=True)


if __name__=='__main__':main()
