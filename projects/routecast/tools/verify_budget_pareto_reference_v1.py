"""Independent exhaustive simple-path oracle, including cycles and zero increments."""
import hashlib, json, random
from pathlib import Path
from budget_pareto_reference_v1 import search


def oracle(adj, source, sink, budget, initial):
    costs=[]
    def visit(u, seen, raw, cost):
        if raw > budget:
            return
        if u == sink:
            costs.append(cost)
            return
        for _, v, r, p in adj.get(u, []):
            if v not in seen:
                visit(v, seen | {v}, raw+r, cost+r+p)
    visit(source, {source}, initial, initial)
    return min(costs) if costs else None

count=0
for seed in range(100):
    rng=random.Random(seed)
    n=6; adj={u: [] for u in range(n)}; eid=0
    for u in range(n):
        for v in range(n):
            if rng.random() < .28:
                adj[u].append((eid,v,rng.randrange(6),rng.randrange(8))); eid+=1
    for source in range(n):
        for sink in range(n):
            for budget in (0,3,8,20):
                initial=seed%3
                expected=oracle(adj,source,sink,budget,initial)
                actual=search(adj,source,sink,budget,initial)
                assert actual['status']==('INFEASIBLE' if expected is None else 'FOUND')
                if expected is not None:
                    assert actual['cost']==expected
                    u=source; raw=cost=initial; seen={u}
                    for edge in actual['edges']:
                        matches=[a for a in adj[u] if a[0]==edge]; assert len(matches)==1
                        _,u,r,p=matches[0]; raw+=r; cost+=r+p
                        assert u not in seen; seen.add(u)
                    assert u==sink and raw==actual['raw']<=budget and cost==expected
                count+=1
# One cheapest label loses the only budget-feasible continuation.
adj={0:[(0,1,5,0),(1,1,1,6)],1:[(2,2,2,0)]}
a=search(adj,0,2,4); assert a['edges']==[1,2] and a['cost']==9
assert search(adj,0,2,4,max_labels=1)['status']=='UNKNOWN_LABEL_LIMIT'
root=Path(__file__).resolve().parents[1]
out=root/'experiments/budget_pareto_reference_v1_2026-10-09'; out.mkdir(exist_ok=False)
sources=[Path(__file__),root/'tools/budget_pareto_reference_v1.py']
r=dict(exhaustive_endpoint_budget_cases=count,all_pass=True,tradeoff_counterexample_pass=True,label_limit_is_unknown=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},scope='Small additive integer graphs only; not original RR integration, shared-parent NET solver, scalability, quality or complete workflow gains.')
(out/'verification.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
