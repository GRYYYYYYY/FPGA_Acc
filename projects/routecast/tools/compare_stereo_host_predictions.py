"""Require complete authenticated artifacts before claiming full host parity."""
import json
from pathlib import Path
from pre_route_endpoints import sha

def run():
    base=Path('experiments/stereo_prospective_validation_2026-10-05')
    name='ordinary_additive_class_cache_prediction_undriven_v2'
    roots=[base/name,base/(name+'_authenticated_host')]
    out=base/'authenticated_host_full_parity.json'
    if out.exists():raise ValueError('fresh result required')
    protocols=[];receipts=[];bindings=[]
    for root in roots:
        p=json.loads((root/'protocol.json').read_text());r=json.loads((root/'receipt.json').read_text())
        assert r['protocol_sha256']==sha(root/'protocol.json')
        assert r['prediction_sha256']==sha(root/'prediction.json')
        assert r['journal_sha256']==sha(root/'net_results.jsonl')
        assert r['connections']==81610 and r['nets']==61314 and r['inputs_unchanged']
        assert all(sha(v['path'])==v['sha256'] for v in p['inputs'].values())
        protocols.append(p);receipts.append(r)
        bindings.append({'path':str(root.resolve()),'receipt_sha256':sha(root/'receipt.json'),
                         'prediction_sha256':r['prediction_sha256'],'journal_sha256':r['journal_sha256']})
    for key in ('inputs','csr_manifest_sha256','frontend_protocol_sha256','policy_sha256','order','method'):
        assert protocols[0][key]==protocols[1][key],key
    assert receipts[0]['failed']==receipts[1]['failed']
    # Equality includes every raw edge witness, method, occupancy and counter.
    assert json.loads((roots[0]/'prediction.json').read_text())==json.loads((roots[1]/'prediction.json').read_text())
    count=0
    with (roots[0]/'net_results.jsonl').open() as a,(roots[1]/'net_results.jsonl').open() as b:
        for line in a:
            other=b.readline();assert other and json.loads(line)==json.loads(other)
            count+=1
        assert not b.readline()
    assert count==61314
    result={'artifacts':bindings,'source_sha256':sha(__file__),'nets':count,'connections':81610,
            'full_prediction_semantically_exact':True,'all_journal_paths_and_counters_exact':True,
            'prediction_bytes_exact':bindings[0]['prediction_sha256']==bindings[1]['prediction_sha256'],
            'timing_observations_s':[r['full_prediction_wall_s'] for r in receipts],
            'scope':'implementation parity only; concurrent shared host timings not controlled speedup; physical legality, QoR and feedback net benefit separate'}
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':run()
