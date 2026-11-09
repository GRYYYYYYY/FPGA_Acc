"""Exact selection within supplied path sets, not unrestricted tree optimization.

Objective: initial RC once plus sum(raw increment + penalty) over union edges.
Bounded enumeration returns UNKNOWN with optional feasible incumbent; no
infeasibility claim outside supplied candidates or after a search limit.
"""
from budget_NET_gate_reference_v1 import audit


def select(adjacency, source, budgets, candidates, initial_raw=0,
           capacities=None, max_states=100000):
    if set(candidates)!=set(budgets) or max_states<1:
        raise ValueError('candidate keys/state cap')
    sinks=sorted(budgets); valid={}; costs={}
    for s in sinks:
        valid[s]=[]
        for path in candidates[s]:
            try: audit(adjacency,source,{s:budgets[s]},{s:path},initial_raw,capacities)
            except ValueError: continue
            u=source
            for edge in path:
                _,v,r,p=next(a for a in adjacency[u] if a[0]==edge)
                key=(u,edge); costs[key]=r+p; u=v
            if tuple(path) not in valid[s]: valid[s].append(tuple(path))
    states=0; limited=False; best=None; best_cost=None
    def visit(i,paths):
        nonlocal states,limited,best,best_cost
        if states>=max_states:
            limited=True; return
        states+=1
        partial_budgets={s:budgets[s] for s in paths}
        try: a=audit(adjacency,source,partial_budgets,paths,initial_raw,capacities)
        except ValueError: return
        cost=initial_raw+sum(costs[(u,e)] for u,e in a['parents'].values())
        if best_cost is not None and cost>=best_cost: return
        if i==len(sinks):
            best={s:list(p) for s,p in paths.items()}; best_cost=cost; return
        s=sinks[i]
        for path in valid[s]:
            visit(i+1,dict(paths,**{} ) | {s:path})
            if limited: return
    visit(0,{})
    return dict(status='UNKNOWN_STATE_LIMIT' if limited else ('OPTIMAL_WITHIN_CANDIDATES' if best is not None else 'NO_COMPATIBLE_CANDIDATE_COMBINATION'), paths=best, union_cost=best_cost, states=states)
