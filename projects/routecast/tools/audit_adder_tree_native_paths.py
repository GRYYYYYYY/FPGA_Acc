"""Evaluator-only arithmetic native physical paths and retained-cohort alignment."""
import argparse
import json
import re
import shutil
import time
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit


def main():
    parser=argparse.ArgumentParser();parser.add_argument('design');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    front=root/'experiments/adder_tree_family_endpoints_2026-10-06'/args.design
    fp=json.loads((front/'protocol.json').read_text());fr=json.loads((front/'receipt.json').read_text())
    assert sha(front/'protocol.json')==fr['protocol_sha256']
    assert all(sha(front/n)==h for n,h in fr['outputs'].items())
    capture=root/'experiments/adder_tree_family_native_capture_v2_2026-10-06'
    cr=json.loads((capture/(args.design+'_receipt.json')).read_text())
    assert cr['exit_code']==0 and not cr['timed_out']
    route=cr['artifacts']['design.route']
    inputs={k:fp['inputs'][k] for k in ('rr_graph','reference_place')}
    inputs['evaluator_route']=route;inputs['endpoints']={'path':str(front/'endpoints.json'),'sha256':fr['outputs']['endpoints.json']}
    assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
    with Path(route['path']).open() as f:header=f.readline()
    match=re.search(r'Placement_ID:\s*SHA256:([0-9a-f]{64})',header)
    assert match and match[1]==inputs['reference_place']['sha256']
    out=root/'experiments/adder_tree_family_native_path_audit_2026-10-06'/args.design;out.mkdir(parents=True)
    (out/'source').mkdir()
    sources={}
    for name in ('audit_adder_tree_native_paths.py','stream_native_route_audit.py','audit_native_route.py','pre_route_endpoints.py'):
        path=root/'tools'/name;shutil.copyfile(path,out/'source'/name);sources[name]=sha(path)
    protocol={'inputs':inputs,'source_sha256':sources,'frontend_receipt_sha256':sha(front/'receipt.json'),
              'case_receipt_sha256':sha(capture/(args.design+'_receipt.json')),
              'scope':'evaluator-only printed native RR arc/switch/union checks and retained SOURCE-SINK multiset; no STA certificate or predictor label input'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    start=time.monotonic();result=audit(inputs['rr_graph']['path'],route['path'])
    ep=json.loads((front/'endpoints.json').read_text());retained={r['net_id'] for r in ep['connections']}
    expected=Counter((r['net_id'],r['source'],r['sink']) for r in ep['connections'])
    actual=Counter((r['net_id'],r['source'],r['sink']) for r in result['connections'] if r['net_id'] in retained)
    missing=expected-actual;extra=actual-expected
    alignment={'retained_connections':sum(expected.values()),'native_retained_occurrences':sum(actual.values()),
               'retained_endpoint_multiset_exact':not missing and not extra,
               'missing':[{'net':n,'source':s,'sink':d,'count':v} for (n,s,d),v in sorted(missing.items())],
               'extra':[{'net':n,'source':s,'sink':d,'count':v} for (n,s,d),v in sorted(extra.items())]}
    (out/'physical_branches.json').write_text(json.dumps(result)+'\n')
    (out/'alignment.json').write_text(json.dumps(alignment,indent=2)+'\n')
    assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
    assert all(sha(root/'tools'/name)==h for name,h in sources.items())
    receipt={'protocol_sha256':sha(out/'protocol.json'),'physical_checks_pass':result['all_printed_branch_arc_switch_and_union_checks_pass'],
             'retained_endpoint_multiset_exact':alignment['retained_endpoint_multiset_exact'],
             'retained_connections':sum(expected.values()),'overflow_units':result['overflow_units'],
             'wall_s':time.monotonic()-start,'outputs':{n:sha(out/n) for n in ('physical_branches.json','alignment.json')},
             'scope':protocol['scope']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
    assert receipt['physical_checks_pass'] and receipt['retained_endpoint_multiset_exact']


if __name__=='__main__':main()
