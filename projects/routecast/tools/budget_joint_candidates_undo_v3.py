"""Iterative candidate enumeration with in-place DFS union and undo frames.
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
    # Deferred branch frames share the current DFS union; undo frames restore
    # it before siblings. Only visit frames consume original search states.
    stack=[('visit',0,None,None,initial_raw)]; parents={};paths={}
    states=0;best=None;best_cost=None
    while stack:
        frame=stack.pop()
        if frame[0]=='undo':
            _,sink,added=frame
            for node in added:del parents[node]
            del paths[sink]
            continue
        if states>=max_states:
            return dict(status='UNKNOWN_STATE_LIMIT',paths=best,union_cost=best_cost,states=states)
        _,i,path,addition,cost=frame;states+=1;added=[];compatible=True
        if addition is not None:
            for node,parent in addition.items():
                if node in parents:
                    if parents[node]!=parent:compatible=False;break
                else:parents[node]=parent;added.append(node);cost+=costs[parent]
            if not compatible:
                for node in added:del parents[node]
                continue
            sink=sinks[i-1];paths[sink]=path
            stack.append(('undo',sink,added))
        if best_cost is not None and cost>=best_cost:continue
        if i==len(sinks):
            best={s:list(p) for s,p in paths.items()};best_cost=cost;continue
        for child_path,child_parents in reversed(valid[sinks[i]]):
            stack.append(('visit',i+1,child_path,child_parents,cost))
    return dict(status='OPTIMAL_WITHIN_CANDIDATES' if best is not None else 'NO_COMPATIBLE_CANDIDATE_COMBINATION',paths=best,union_cost=best_cost,states=states)
