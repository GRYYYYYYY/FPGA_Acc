"""Iterative candidate enumeration with incremental parent union.
Same frozen candidate order, objective, pruning and state-limit semantics as v1.
Path safety audited once per candidate; no repeated partial path traversal.
"""
from budget_NET_gate_reference_v1 import audit


def select(adjacency, source, budgets, candidates, initial_raw=0,
           capacities=None, max_states=100000):
    if set(candidates)!=set(budgets) or max_states<1:
        raise ValueError('candidate keys/state cap')
    sinks=sorted(budgets); valid={}; costs={}
    for s in sinks:
        valid[s]=[]; seen=set()
        for path in candidates[s]:
            try: a=audit(adjacency,source,{s:budgets[s]},{s:path},initial_raw,capacities)
            except ValueError: continue
            path=tuple(path)
            if path in seen: continue
            seen.add(path)
            u=source
            for edge in path:
                _,v,r,p=next(arc for arc in adjacency[u] if arc[0]==edge)
                costs[(u,edge)]=r+p;u=v
            valid[s].append((path,a['parents']))
    stack=[(0,{}, {},initial_raw)]; states=0; best=None;best_cost=None
    while stack:
        if states>=max_states:
            return dict(status='UNKNOWN_STATE_LIMIT',paths=best,union_cost=best_cost,states=states)
        i,paths,parents,cost=stack.pop();states+=1
        if parents is None:continue
        if best_cost is not None and cost>=best_cost:continue
        if i==len(sinks):
            best={s:list(p) for s,p in paths.items()};best_cost=cost;continue
        s=sinks[i]
        # Reverse push keeps v1 depth-first candidate traversal and exact tie behavior.
        for path,addition in reversed(valid[s]):
            merged=dict(parents);total=cost;compatible=True
            for v,parent in addition.items():
                if v in merged:
                    if merged[v]!=parent:compatible=False;break
                else:merged[v]=parent;total+=costs[parent]
            stack.append((i+1,paths|{s:path},merged if compatible else None,total))
    return dict(status='OPTIMAL_WITHIN_CANDIDATES' if best is not None else 'NO_COMPATIBLE_CANDIDATE_COMBINATION',paths=best,union_cost=best_cost,states=states)
