"""Independent forward Dijkstra and complete directed physical-slot audit."""
import heapq
import json
import random
import sys
from pathlib import Path
from bidirectional_rc_reference_v1 import Bidirectional
from pre_route_endpoints import sha
R = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
bindings = closure([Path(__file__)])
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
            inc.append(rng.choice([0,0,1,5,2**63]))
        f['row_offsets'].append(len(inc))
    search = Bidirectional(f,inc)
    enabled = [u for u,c in enumerate(f['capacities']) if c]
    for step in range(12):
        source,sink = rng.choice(enabled),rng.choice(enabled)
        if step==0:
            sink = source
        weight = rng.choice([0,1,13,2**63])
        prices = {u:rng.choice([0,1,7,2**63]) for u in range(n)}
        initial = rng.randrange(9)
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
        result = search.search(source,sink,prices,weight,initial)
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
assert all(sha(p)==h for p,h in bindings.items())
D = R/'experiments/bidirectional_rc_reference_contract_v1_2026-10-08'
D.mkdir(exist_ok=False)
result = dict(bindings=bindings,pass_all=True,graphs=200,queries=queries,
              reachable=reachable,unreachable=queries-reachable,
              scope='Python single-target reference only; no C++/real graph/full model or performance proof')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
