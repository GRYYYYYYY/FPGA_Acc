"""Exhaustive owner-domain theorem and closure checks on small complete banks."""
import itertools,json
from pathlib import Path
from NET_candidate_ownership_implications_v1 import build,close,components
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/NET_candidate_ownership_implications_contract_v1_2026-10-19';out.mkdir(exist_ok=False)
    # Exhaust every owner-subset pair and choice on three NETs, including
    # inherited overuse, owner absence and capacity-two exclusions.
    nodes=tuple(range(3));subsets=[set(x for x in nodes if mask>>x&1) for mask in range(8)];checks=0
    for a,b,cap in itertools.product(subsets,subsets,[1,2]):
        g=build(nodes,{0:a},{0:b},[cap])
        for chosen in subsets:
            mixed=len(a-chosen)+len(b&chosen)
            violations=[(u,v) for u,v in g['edges'] if u in chosen and v not in chosen]
            if cap==1 and len(a)==len(b)==1:assert (mixed>cap)==bool(violations)
            else:assert not g['edges']
            closed=close(g,chosen);assert chosen<=closed and close(g,closed)==closed
            assert all(u not in closed or v in closed for u,v in g['edges'])
            # Closure is the least closed superset, not arbitrary all-B repair.
            for alternative in subsets:
                if chosen<=alternative and all(u not in alternative or v in alternative for u,v in g['edges']):assert closed<=alternative
            checks+=1
    # All 2^12 directed graphs on four vertices, with independent transitive
    # reachability checking SCC equivalence and closures for all16 seed masks.
    nodes=tuple(range(4));possible=[(u,v) for u in nodes for v in nodes if u!=v];graphs=0
    for mask in range(1<<len(possible)):
        edges=tuple(e for i,e in enumerate(possible) if mask>>i&1);g={'nodes':nodes,'edges':edges};reach=[[u==v or (u,v) in edges for v in nodes] for u in nodes]
        for k in nodes:
            for u in nodes:
                for v in nodes:reach[u][v]=reach[u][v] or reach[u][k] and reach[k][v]
        groups=components(g);groupid={u:i for i,group in enumerate(groups) for u in group};assert set(groupid)==set(nodes)
        for u,v in itertools.product(nodes,repeat=2):assert (groupid[u]==groupid[v])==(reach[u][v] and reach[v][u])
        for seedmask in range(16):
            seeds={u for u in nodes if seedmask>>u&1};expected={v for u in seeds for v in nodes if reach[u][v]};assert close(g,seeds)==expected
        graphs+=1
    paths=[Path(__file__).resolve(),R/'tools/NET_candidate_ownership_implications_v1.py']
    (out/'verification.json').write_text(json.dumps(dict(status='EXHAUSTIVE_OWNER_CAPACITY_THEOREM_MINIMAL_CLOSURE_AND_SCC_PASS',owner_choice_checks=checks,directed_graphs=graphs,closure_seed_checks=graphs*16,bindings={str(p):sha(p) for p in paths},scope='Capacity1 and exactly one owner per bank domain only; not general capacity or inherited-overuse legalization.'),indent=2)+'\n');print('OWNERSHIP_IMPLICATION_CONTRACT_PASS',checks,graphs,flush=True)


if __name__=='__main__':main()
