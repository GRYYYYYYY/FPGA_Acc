"""Independent all-pin accounting for arithmetic pre-route endpoints."""
import argparse
import collections
import json
import shutil
from pathlib import Path
from pre_route_endpoints import sha


def main():
    parser=argparse.ArgumentParser();parser.add_argument('design');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    base=root/'experiments/constant_multiplier_family_endpoints_cw32_2026-10-06'/args.design
    p=json.loads((base/'protocol.json').read_text());r=json.loads((base/'receipt.json').read_text())
    assert sha(base/'protocol.json')==r['protocol_sha256']
    assert all(sha(base/name)==h for name,h in r['outputs'].items())
    assert all(sha(base/'source'/name)==h for name,h in p['sources'].items())
    assert all(sha(v['path'])==v['sha256'] for v in p['inputs'].values())
    ep=json.loads((base/'endpoints.json').read_text());mapping=json.loads((base/'mapping.json').read_text())
    source=collections.defaultdict(list);sinks=collections.defaultdict(list);seen=set()
    for row in mapping['pin_details']:
        key=(row['block_id'],row['port'],row['bit'],row['role']);assert key not in seen;seen.add(key)
        assert ep['net_names'][str(row['net_id'])]==row['net']
        assert row['role'] in ('SOURCE','SINK')
        (source if row['role']=='SOURCE' else sinks)[row['net_id']].append(row)
    assert all(len(rows)==1 for rows in source.values()) and set(sinks)<=set(source)
    clocks={row['net_id']:row for row in ep['excluded_nets']}
    assert len(clocks)==len(ep['excluded_nets'])
    for nid,row in clocks.items():assert row['sink_pins']==len(sinks[nid])
    globals=set(ep['nonclock_global_excluded_net_ids'])
    assert globals=={r['net_id'] for r in mapping['nonclock_global_receiver_pins']}
    excluded=set(clocks)|globals
    expected=collections.Counter((nid,source[nid][0]['rr_node'],row['rr_node']) for nid,rows in sinks.items() if nid not in excluded for row in rows)
    actual=collections.Counter((row['net_id'],row['source'],row['sink']) for row in ep['connections'])
    assert expected==actual
    assert [row['connection_id'] for row in ep['connections']]==list(range(len(ep['connections'])))
    total=sum(len(rows) for rows in sinks.values());dropped=sum(len(sinks[nid]) for nid in excluded)
    assert total==len(ep['connections'])+dropped
    out=root/'experiments/constant_multiplier_family_endpoint_accounting_cw32_2026-10-06'/args.design;out.mkdir(parents=True)
    shutil.copyfile(__file__,out/'source.py')
    result={'frontend_receipt_sha256':sha(base/'receipt.json'),'source_sha256':sha(__file__),
            'logical_sink_pins':total,'retained_connections':len(ep['connections']),'excluded_sink_pins':dropped,
            'physical_pin_details':len(mapping['pin_details']),'source_only_nets':len(set(source)-set(sinks)),
            'all_pin_accounting_and_endpoint_multisets_match':True,
            'scope':'mapped logical pin accounting only; not independent RR physical pin membership or native route alignment'}
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
