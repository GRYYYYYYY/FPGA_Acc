"""Pure all-or-nothing NET admission for small additive graphs; no state mutation.

Caller supplies the full sink/budget mapping and independently established old
paths. Admission does not promise joint-tree optimality or demand improvement.
"""

def audit(adjacency, source, budgets, paths, initial_raw=0, capacities=None):
    if set(paths) != set(budgets):
        raise ValueError('QUERY_SET')
    parents={}; demand=set(); delays={}
    for sink, budget in budgets.items():
        u=source; seen={source}; raw=initial_raw; demand.add(source)
        if raw < 0 or budget < 0:
            raise ValueError('NEGATIVE_RC')
        for edge in paths[sink]:
            matches=[a for a in adjacency.get(u, ()) if a[0]==edge]
            if len(matches)!=1:
                raise ValueError('ARC')
            _,v,r,p=matches[0]
            if r < 0 or p < 0:
                raise ValueError('NEGATIVE_INCREMENT')
            if v in seen:
                raise ValueError('CYCLE')
            parent=(u,edge)
            if v in parents and parents[v]!=parent:
                raise ValueError('MULTIPLE_PARENTS')
            parents[v]=parent; raw+=r; seen.add(v); demand.add(v); u=v
        if u!=sink:
            raise ValueError('ENDPOINT')
        if raw>budget:
            raise ValueError('BUDGET')
        delays[sink]=raw
    if capacities is not None and any(capacities.get(v,0)<=0 for v in demand):
        raise ValueError('CAPACITY')
    return dict(parents=parents, unique_NET_nodes=sorted(demand), delays=delays)


def decide(adjacency, source, budgets, old_paths, candidate_paths,
           initial_raw=0, capacities=None):
    old=audit(adjacency,source,budgets,old_paths,initial_raw,capacities)
    try:
        candidate=audit(adjacency,source,budgets,candidate_paths,initial_raw,capacities)
    except ValueError as error:
        return dict(status='RETAIN', reason=str(error), paths=old_paths, audit=old)
    return dict(status='ADMIT', reason='ALL_NET_CONTRACTS_PASS', paths=candidate_paths, audit=candidate)
