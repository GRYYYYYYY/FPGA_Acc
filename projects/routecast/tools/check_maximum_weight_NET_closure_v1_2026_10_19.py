"""Exhaustive small optima, large weights, cycles and corrupted certificate checks."""
import itertools,json,random,copy
from pathlib import Path
from maximum_weight_NET_closure_v1 import solve,verify
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/maximum_weight_NET_closure_contract_v1_2026-10-19';out.mkdir(exist_ok=False);checks=0
    nodes=tuple(range(3));possible=[(u,v) for u in nodes for v in nodes if u!=v]
    cases=[]
    for mask in range(64):
        edges=[e for i,e in enumerate(possible) if mask>>i&1]
        for values in itertools.product([-1,0,1],repeat=3):cases.append((dict(zip(nodes,values)),edges))
    rng=random.Random(6119)
    for i in range(300):
        ns=range(6);cases.append(({n:rng.randint(-20,20) for n in ns},[(u,v) for u in ns for v in ns if u!=v and rng.randrange(5)==0]))
    cases.extend([({},[]),({0:2**150,1:-(2**149)},[(0,1)]),({0:5,1:-7,2:6},[(0,1),(1,2),(2,0)])])
    for weights,edges in cases:
        cert=solve(weights,edges);actual=verify(weights,edges,cert);ns=sorted(weights);best=None
        for mask in range(1<<len(ns)):
            chosen={u for i,u in enumerate(ns) if mask>>i&1}
            if all(u not in chosen or v in chosen for u,v in edges):
                value=sum(weights[n] for n in chosen);best=value if best is None else max(best,value)
        assert actual==best;checks+=1
    # Protocol's scaled objective must first maximize demand reduction and
    # then minimize number of B NETs, including negative dependency weights.
    for values in itertools.product([-1,0,1],repeat=3):
        edges=[(0,1),(1,2)];weights={i:4*values[i]-1 for i in range(3)};cert=solve(weights,edges);chosen=set(cert['selected'])
        feasible=[s for s in [set(i for i in range(3) if m>>i&1) for m in range(8)] if all(u not in s or v in s for u,v in edges)]
        expected=max((sum(values[i] for i in s),-len(s)) for s in feasible);assert (sum(values[i] for i in chosen),-len(chosen))==expected
    base=solve({0:8,1:-3},[(0,1)]);rejected=0
    for fault in ['flow','capacity','cut','objective']:
        bad=copy.deepcopy(base)
        if fault=='flow':bad['arcs'][0]['flow']+=1
        elif fault=='capacity':bad['arcs'][0]['capacity']+=1
        elif fault=='cut':bad['source_side'].append(bad['sink'])
        else:bad['objective']+=1
        try:verify({0:8,1:-3},[(0,1)],bad)
        except AssertionError:rejected+=1
        else:raise AssertionError('corrupted certificate accepted')
    assert rejected==4
    paths=[Path(__file__).resolve(),R/'tools/maximum_weight_NET_closure_v1.py'];(out/'verification.json').write_text(json.dumps(dict(status='EXHAUSTIVE_AND_RANDOM_CLOSURE_OPTIMA_FLOW_CUT_CERTIFICATES_TIES_AND_CORRUPTION_PASS',optimum_checks=checks,lexicographic_checks=27,corrupted_rejections=rejected,bindings={str(p):sha(p) for p in paths}),indent=2)+'\n');print('MAX_WEIGHT_CLOSURE_CONTRACT_PASS',checks,flush=True)


if __name__=='__main__':main()
