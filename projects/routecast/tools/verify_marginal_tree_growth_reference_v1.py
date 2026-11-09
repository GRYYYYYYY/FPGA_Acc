"""Exhaustive simple-extension oracle for small cyclic directed graphs."""
import json,sys,random
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from marginal_tree_growth_reference_v1 import grow
from pre_route_endpoints import sha
rng=random.Random(10408);checked=0;cases=0
for case in range(160):
    size=7;adj={n:[] for n in range(size)};edges={};inc={};eid=0
    for u in range(size):
        for v in range(size):
            if u!=v and (v==u+1 or rng.random()<0.22):
                adj[u].append((eid,v));edges[eid]=(u,v);inc[eid]=rng.randrange(1,10);eid+=1
    cap={n:1 for n in range(size)};prices={n:rng.randrange(4) for n in range(size)}
    sinks=rng.sample(list(range(1,size)),3);weight=3;initial=5
    result=grow(0,sinks,adj,inc,cap,prices,weight,initial,{n:10000 for n in sinks})
    assert result['status']=='CANDIDATE';owned={0};parents={};raw={0:initial}
    for branch in result['branches']:
        sink=branch['sink'];allcosts=[]
        def visit(u,seen,cost):
            if u==sink:allcosts.append(cost);return
            for e,v in adj[u]:
                if v not in owned and v not in seen and cap[v]>0:
                    visit(v,seen|{v},cost+inc[e]+weight*prices[v])
        for attachment in owned:visit(attachment,{attachment},0)
        assert allcosts and branch['incremental_cost']==min(allcosts)
        u=branch['attachment'];assert u in owned
        total=0
        for e in branch['new_edges']:
            p,v=edges[e];assert p==u and v not in owned
            parents[v]=(p,e);raw[v]=raw[p]+inc[e];owned.add(v);u=v
            total+=inc[e]+weight*prices[v]
        assert u==sink and total==branch['incremental_cost'];checked+=1
    assert result['parent']==parents and result['raw']==raw and set(result['owned'])==owned
    assert [x['sink'] for x in result['records']]==sinks
    for record in result['records']:
        u=0;delay=initial
        for e in record['edges']:
            p,v=edges[e];assert p==u;u=v;delay+=inc[e]
        assert u==record['sink'] and delay==record['delay']
    cases+=1
# Budget failure after a successful first branch must expose no partial candidate.
failed=grow(0,[1,2],{0:[(0,1)],1:[(1,2)]},{0:4,1:4},{0:1,1:1,2:1},{},0,2,{1:10,2:9})
assert failed['status']=='RETAIN_OLD_TREE_BUDGET' and 'records' not in failed and failed['delay']==10
unreachable=grow(0,[2],{0:[(0,1)]},{0:4},{0:1,1:0,2:1},{},0,2,{2:99})
assert unreachable['status']=='RETAIN_OLD_TREE_UNREACHABLE' and 'records' not in unreachable
out=R/'experiments/marginal_tree_growth_reference_contract_v1_2026-10-08';out.mkdir()
files=[Path(__file__),R/'tools/marginal_tree_growth_reference_v1.py',R/'experiments/ethernet_marginal_tree_growth_prereg_v1_2026-10-08/protocol.json']
bindings={str(p):sha(p) for p in files}
(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,random_cyclic_graphs=cases,exhaustive_minimum_incremental_branch_checks=checked,all_parent_prefix_paths_and_delay_checks_pass=True,budget_and_zero_capacity_failures_no_partial_candidate_pass=True,scope='Small-graph reference contract only. Does not prove full native graph RC/tree replacement correctness, global tree optimality or constrained feasibility.'),indent=2)+'\n')
print('PASS reference exhaustive',cases,checked)
