"""Deterministic interface invalidation and bounded retention contract, not RR performance."""
import json
from pathlib import Path
from types import SimpleNamespace
import whole_net_zero_price_search_cache_v2 as m
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/whole_net_initial_cache_boundaries_v2_2026-10-10';assert not D.exists();D.mkdir()
calls=[]
def fake(self, source, sinks):
    calls.append((source,sorted(sinks)))
    return {t:100+t for t in sinks},{t:(source,t) for t in sinks},set(sinks)
def prepare(self,prices,weight):pass
m.Original.search=fake;m.Original.prepare=prepare
q=lambda net,sink,cid:dict(net_id=net,source=0,sink=sink,connection_id=cid)
def run(qs,digest='g1',scale=100,impl='h1'):
    x=object.__new__(m.Search);x.rc=SimpleNamespace(scale=scale)
    x.configure_initial_groups(digest,qs,{'implementation':impl})
    answers=[]
    for net in sorted({q['net_id'] for q in qs}):
        group=[q for q in qs if q['net_id']==net]
        answers.append(x.search(group[0]['source'],{q['sink'] for q in group}))
    return x,answers
m.reset();qs=[q(1,1,1),q(1,2,2),q(2,3,3)]
x,a=run(qs);assert len(calls)==2
_,b=run(qs);assert a==b and len(calls)==2
b[0][1].clear();_,c=run(qs);assert c==a and len(calls)==2
changed=[q(1,1,1),q(1,4,2),q(2,3,3)];run(changed);assert len(calls)==3
run(changed,digest='g2');assert len(calls)==5
run(changed,digest='g2',scale=101);assert len(calls)==7
x,_=run(changed,digest='g2',scale=101,impl='h2');assert len(calls)==9
x.prepare({1:1},1);x.search(0,{1,4});assert len(calls)==10
# Small limits force eviction; oversized groups are searched completely and not retained.
m.reset();m._LIMITS.update(groups=1,parents=2,queries=2)
run(qs);assert m.diagnostics()['capacity_evictions']==1
run(qs);assert m.diagnostics()['cached_groups']<=1
run([q(1,1,1),q(1,2,2),q(1,3,3)]);assert m.diagnostics()['oversize_uncached']==1
assert m.diagnostics()['cached_groups']==0
v=dict(all_identity_and_whole_net_invalidation_checks_pass=True,returned_mutation_cannot_poison_cache=True,feedback_always_fresh=True,capacity_eviction_and_oversize_full_search_pass=True,scope='Synthetic requested-path interface contract; real full SHA parity and multi-layout performance not established.',bindings={str(p):sha(p) for p in [Path(__file__).resolve(),R/'tools/whole_net_zero_price_search_cache_v2.py']})
(D/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print('BOUNDARY CONTRACT PASS')
