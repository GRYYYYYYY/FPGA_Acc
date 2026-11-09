"""Independent forward Dijkstra and complete directed physical-slot audit."""
import heapq
import json
import random
import sys
from pathlib import Path
from bidirectional_rc_reference_v2 import Bidirectional as Reference
from hybrid_bidirectional_search_v1 import Search
from soft_demand_workspace_bridge_v1 import Search as Forward
from types import SimpleNamespace
from pre_route_endpoints import sha
R = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
binary=R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so'
bindings = {**closure([Path(__file__)]),str(binary):sha(binary),**{str(R/'tools/soft_demand_cpp'/name):sha(R/'tools/soft_demand_cpp'/name) for name in ['bidirectional_workspace_v2.cpp','tree_workspace_radix_stats_v4.cpp']}}
queries = reachable = 0
for seed in range(200):
    rng = random.Random(seed)
    n = rng.randrange(2,35)
    f = dict(capacities=[rng.randrange(3) for _ in range(n)],row_offsets=[0],dest_ranks=[])
    f['capacities'][0] = 1
    inc = []
    for u in range(n):
        for _ in range(rng.randrange(n+1)):
            f['dest_ranks'].append(rng.randrange(n))
            inc.append(rng.choice([0,0,1,5,2**40]))
        f['row_offsets'].append(len(inc))
    reference = Reference(f,inc)
    rc=SimpleNamespace(increments=inc,initial=lambda node:node%9)
    forward_binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so'
    bindings[str(forward_binary)]=sha(forward_binary)
    search = Search(f,rc,forward_binary)
    forward=Forward(f,rc,forward_binary)
    enabled = [u for u,c in enumerate(f['capacities']) if c]
    for step in range(12):
        source,sink = rng.choice(enabled),rng.choice(enabled)
        if step==0:
            sink = source
        weight = rng.choice([0,1,13,2**63])
        prices = {u:rng.choice([0,1,7,2**40]) for u in range(n)}
        initial = source%9
        dist,q = {source:initial},[(initial,source)]
        expected = None
        while q:
            cost,u = heapq.heappop(q)
            if cost!=dist[u]:
                continue
            if u==sink:
                expected = cost
                break
            for e in range(f['row_offsets'][u],f['row_offsets'][u+1]):
                v = f['dest_ranks'][e]
                if not f['capacities'][v]:
                    continue
                value = cost+inc[e]+weight*prices[v]
                if v not in dist or value<dist[v]:
                    dist[v] = value
                    heapq.heappush(q,(value,v))
        search.prepare(prices,weight)
        raw,parents,settled=search.search(source,{sink})
        result=None
        if sink in settled:
            u=sink;slots=[]
            while u!=source:u,e=parents[u];slots.append(e)
            slots.reverse()
            result=dict(slots=slots,raw=raw[sink],objective=raw[sink]+weight*sum(prices[f['dest_ranks'][e]] for e in slots))
        ref=reference.search(source,sink,prices,weight,initial)
        assert (result is None)==(ref is None)
        if ref is not None:assert all(result[k]==ref[k] for k in result)
        targets=set(rng.sample(enabled,min(len(enabled),rng.randrange(3,6))))
        if len(targets)>1:
            forward.prepare(prices,weight)
            a_raw,a_parents,a_settled=search.search(source,targets)
            b_raw,b_parents,b_settled=forward.search(source,targets)
            assert a_settled==b_settled
            assert list(a_raw)==list(b_raw)
            assert list(search.forward.pn)==list(forward.pn) and list(search.forward.pe)==list(forward.pe)
        queries += 1
        if expected is None:
            assert result is None
            continue
        reachable += 1
        assert result is not None and result['objective']==expected
        u,raw,cost,seen = source,initial,initial,{source}
        for e in result['slots']:
            assert f['row_offsets'][u]<=e<f['row_offsets'][u+1]
            u = f['dest_ranks'][e]
            assert f['capacities'][u] and u not in seen
            seen.add(u)
            raw += inc[e]
            cost += inc[e]+weight*prices[u]
        assert u==sink and raw==result['raw'] and cost==expected
    search.close();forward.close()
assert all(sha(p)==h for p,h in bindings.items())
D = R/'experiments/hybrid_bidirectional_search_contract_v1_2026-10-08'
D.mkdir(exist_ok=False)
result = dict(bindings=bindings,pass_all=True,graphs=200,queries=queries,
              reachable=reachable,unreachable=queries-reachable,
              scope='Hybrid requested singleton paths versus reference/independent Dijkstra; multi-target full arrays versus original forward. No full model proof')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
