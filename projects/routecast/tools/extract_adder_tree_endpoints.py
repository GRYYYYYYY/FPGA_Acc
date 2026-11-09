"""Pre-route physical-class endpoints for a completed frozen arithmetic capture."""
import argparse
import json
import shutil
from pathlib import Path
from pre_route_endpoints import extract, sha
from nonclock_global_pins import classify


def main():
    parser=argparse.ArgumentParser();parser.add_argument('design');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    capture=root/'experiments/adder_tree_family_native_capture_v2_2026-10-06'
    protocol=json.loads((capture/'protocol.json').read_text())
    assert args.design in protocol['cohort']
    case=json.loads((capture/(args.design+'_receipt.json')).read_text())
    assert case['exit_code']==0 and not case['timed_out'] and case['input_unchanged']
    artifacts=case['artifacts']
    selected={key:artifacts[name] for key,name in [('atom','design.blif'),('packed_netlist','design.net'),('reference_place','design.place'),('rr_graph','rr_graph.xml')]}
    selected['architecture']=protocol['architecture']
    assert all(sha(v['path'])==v['sha256'] for v in selected.values())
    out=root/'experiments/adder_tree_family_endpoints_2026-10-06'/args.design
    out.mkdir(parents=True)
    (out/'source').mkdir()
    names=['extract_adder_tree_endpoints.py','pre_route_endpoints.py','nonclock_global_pins.py']
    for name in names:shutil.copyfile(root/'tools'/name,out/'source'/name)
    ep,mapping=extract(selected['packed_netlist']['path'],selected['reference_place']['path'],selected['rr_graph']['path'])
    globals=classify(mapping,selected['packed_netlist']['path'],selected['architecture']['path'],selected['rr_graph']['path'])
    global_ids={r['net_id'] for r in globals}
    old_count=len(ep['connections']);ep['connections']=[r for r in ep['connections'] if r['net_id'] not in global_ids]
    for i,r in enumerate(ep['connections']):r['connection_id']=i
    ep['nonclock_global_excluded_net_ids']=sorted(global_ids)
    mapping['nonclock_global_receiver_pins']=globals
    p={'inputs':selected,'capture_protocol_sha256':sha(capture/'protocol.json'),
       'case_receipt_sha256':sha(capture/(args.design+'_receipt.json')),
       'sources':{name:sha(out/'source'/name) for name in names},
       'scope':'packed netlist/placement/RR physical class mapping only; native route never read; architecture-declared global whole nets excluded'}
    (out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
    (out/'endpoints.json').write_text(json.dumps(ep,indent=2)+'\n')
    (out/'mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
    assert all(sha(v['path'])==v['sha256'] for v in selected.values())
    result={'protocol_sha256':sha(out/'protocol.json'),'connections':len(ep['connections']),
            'retained_nets':len({r['net_id'] for r in ep['connections']}),'physical_pin_details':len(mapping['pin_details']),
            'architecture_global_nets':len(global_ids),'removed_global_connections':old_count-len(ep['connections']),
            'outputs':{name:sha(out/name) for name in ('endpoints.json','mapping.json')},
            'native_alignment_verified':False,'full_pin_accounting_verified':False,'unseen_family_claim':False}
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':main()
