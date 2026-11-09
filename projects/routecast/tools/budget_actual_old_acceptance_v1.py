"""Pure bounded selection with current old tree as feasible fallback.
Strict union-objective improvement only; no epoch/ledger mutation or gain claim.
"""
from budget_NET_gate_reference_v1 import audit
from budget_joint_candidates_incremental_v2 import select


def choose(adjacency,source,budgets,old_paths,candidates,initial_raw=0,
           capacities=None,max_states=10000):
    old_audit=audit(adjacency,source,budgets,old_paths,initial_raw,capacities)
    if set(candidates)!=set(budgets):raise ValueError('candidate query set')
    def objective(tree):
        total=initial_raw
        for v,(u,e) in tree['parents'].items():
            arc=next(a for a in adjacency[u] if a[0]==e)
            assert arc[1]==v
            total+=arc[2]+arc[3]
        return total
    old_cost=objective(old_audit)
    supplied={s:[list(old_paths[s])]+[list(p) for p in candidates[s]] for s in budgets}
    answer=select(adjacency,source,budgets,supplied,initial_raw,capacities,max_states)
    chosen={s:list(p) for s,p in old_paths.items()};chosen_audit=old_audit;cost=old_cost;status='RETAIN'
    if answer['paths'] is not None:
        check=audit(adjacency,source,budgets,answer['paths'],initial_raw,capacities)
        proposed=objective(check);assert proposed==answer['union_cost']
        if proposed<old_cost:
            chosen={s:list(p) for s,p in answer['paths'].items()};chosen_audit=check;cost=proposed;status='ACCEPT_STRICT_IMPROVEMENT'
    return dict(status=status,paths=chosen,audit=chosen_audit,old_union_cost=old_cost,chosen_union_cost=cost,search_status=answer['status'],states=answer['states'])
