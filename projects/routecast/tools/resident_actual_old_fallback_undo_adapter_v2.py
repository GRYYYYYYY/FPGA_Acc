"""Resident CSR/exact-RC adapter, pure candidate construction; no state commit."""
from budget_actual_old_acceptance_undo_v2 import choose


def fallback(fields,rc,slots,queries,old_records,parents,settled,prices,weight,max_states=10000):
    if not queries or weight<0:raise ValueError('queries/price weight')
    oldbyid={x['connection_id']:x for x in old_records}
    if len(oldbyid)!=len(old_records) or set(oldbyid)!={q['connection_id'] for q in queries}:raise ValueError('old query set')
    source=queries[0]['source'];budgets={};old_paths={};candidates={};adj={};capacities={source:fields['capacities'][source]}
    def add(path,sink):
        u=source
        for eid in path:
            slot=slots[eid]
            if not fields['row_offsets'][u]<=slot<fields['row_offsets'][u+1]:raise ValueError('CSR source mismatch')
            v=fields['dest_ranks'][slot];arc=(eid,v,rc.increment(slot),weight*prices.get(v,0))
            adj.setdefault(u,{})[eid]=arc;capacities[v]=fields['capacities'][v];u=v
        if u!=sink:raise ValueError('CSR endpoint mismatch')
    for q in queries:
        old=oldbyid[q['connection_id']]
        if q['source']!=source or any(old[k]!=v for k,v in q.items()):raise ValueError('old query metadata')
        sink=q['sink'];path=old['answer']['physical_edge_ids'];budget=old['budget_integer']
        if sink in budgets and (budgets[sink]!=budget or old_paths[sink]!=path):raise ValueError('duplicate sink contract')
        budgets[sink]=budget;old_paths[sink]=path;candidates.setdefault(sink,[])
        add(path,sink)
        if rc.path(source,sink,path)!=old['answer']['delay']:raise ValueError('old RC mismatch')
        if sink in settled:
            u=sink;seen={u};attempt=[]
            while u!=source:
                previous,slot=parents[u]
                if not fields['row_offsets'][previous]<=slot<fields['row_offsets'][previous+1] or fields['dest_ranks'][slot]!=u:raise ValueError('attempt parent arc')
                attempt.append(fields['edge_ids'][slot]);u=previous
                if u in seen:raise ValueError('attempt cycle')
                seen.add(u)
            attempt.reverse();add(attempt,sink);candidates[sink].append(attempt)
    answer=choose({u:list(arcs.values()) for u,arcs in adj.items()},source,budgets,old_paths,candidates,rc.initial(source),capacities,max_states)
    records=[]
    for q in queries:
        old=oldbyid[q['connection_id']];path=answer['paths'][q['sink']];delay=rc.path(source,q['sink'],path)
        assert delay==answer['audit']['delays'][q['sink']]<=old['budget_integer']
        records.append(dict(old,answer=dict(status='FOUND',physical_edge_ids=list(path),delay=delay)))
    return dict(records=records,status=answer['status'],old_union_cost=answer['old_union_cost'],chosen_union_cost=answer['chosen_union_cost'],search_status=answer['search_status'],states=answer['states'])
