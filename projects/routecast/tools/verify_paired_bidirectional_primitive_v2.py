"""Authenticate complete paired observations and independently recompute summaries."""
import json
import math
import statistics
import sys
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/paired_bidirectional_primitive_v2_2026-10-08'/sys.argv[1]
def load(p):return json.loads(p.read_text())
r,p=load(D/'receipt.json'),load(D/'protocol.json')
for d in [r,p]:
    for section in ['bindings','files']:
        for path,h in d.get(section,{}).items():assert sha(path)==h,path
assert r['bindings']==p['bindings'] and r['scope']==p['scope']
assert p['pairs']==5 and len(r['pairs'])==5
expected_order=[['baseline','candidate'] if i%2==0 else ['candidate','baseline'] for i in range(5)]
assert p['order']==expected_order and p['phases']==['initial','round0','round1']
ratios=[];observations=[]
for i,pair in enumerate(r['pairs']):
    assert pair==load(D/f'pair{i}.json')
    assert pair['pair']==i and pair['order']==expected_order[i]
    assert set(pair['arms'])=={'baseline','candidate'}
    for mode,arm in pair['arms'].items():
        assert arm['all_frozen_paths_exact']
        assert [x['phase'] for x in arm['phases']]==p['phases']
        assert all(x['complete_nets']==p['complete_nets'] for x in arm['phases'])
        values=[arm['setup_seconds'],arm['total_seconds']]+[x['seconds'] for x in arm['phases']]
        assert all(math.isfinite(x) and x>0 for x in values)
        subtotal=arm['setup_seconds']+sum(x['seconds'] for x in arm['phases'])
        assert arm['total_seconds']>=subtotal
        observations.append(dict(pair=i,mode=mode,unattributed_seconds=arm['total_seconds']-subtotal))
    ratio=pair['arms']['candidate']['total_seconds']/pair['arms']['baseline']['total_seconds']
    assert ratio==pair['ratio'];ratios.append(ratio)
median=statistics.median(ratios);faster=sum(x<1 for x in ratios)
assert median==r['median_ratio'] and faster==r['candidate_faster_pairs']
bindings={**r['bindings'],**r['files'],str(D/'receipt.json'):sha(D/'receipt.json'),str(Path(__file__)):sha(Path(__file__))}
assert all(sha(path)==h for path,h in bindings.items())
result=dict(bindings=bindings,complete_five_pairs_arithmetic_pass=True,median_ratio=median,
            candidate_faster_pairs=faster,ratios=ratios,observations=observations,
            scope=p['scope']+' Timing is archived producer observation, not independently remeasured. Path proof inherits authenticated complete frozen XML-certified outputs.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','observations']},indent=2))
