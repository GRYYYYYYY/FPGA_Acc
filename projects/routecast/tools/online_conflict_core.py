"""Candidate-local conflict observations and bounded cumulative detour control.

No file lookup, native publication, timing oracle or concurrent state mutation.
The caller owns staged routing, allocation and evidence persistence.
"""
import heapq
from collections import Counter,defaultdict

def shortest_delay(ctx,source,sink,forbidden):
    fields=ctx.rc.fields;dist={};pred={};queue=[]
    if source not in forbidden and fields['capacities'][source]>0:
        dist[source]=0;queue=[(0,source)]
    slot_source={s:u for u in range(len(ctx.context[2])) for s in range(fields['row_offsets'][u],fields['row_offsets'][u+1])}
    while queue:
        value,u=heapq.heappop(queue)
        if value!=dist[u]:continue
        for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
            v=fields['dest_ranks'][slot]
            if v in forbidden or fields['capacities'][v]<=0:continue
            proposed=value+ctx.rc.increments[slot]
            if v not in dist or proposed<dist[v]:
                dist[v]=proposed;pred[v]=slot;heapq.heappush(queue,(proposed,v))
    path=[];node=sink
    if node in dist:
        while node!=source:path.append(node);node=slot_source[pred[node]]
        path.append(source);path.reverse()
    return dict(minimum=dist.get(sink),path_nodes=path,distances=dist,predecessor_slots=pred)

def observe_conflict(ctx,candidate,restrictions,budget):
    failure=candidate.get('failure')
    if not failure or failure['status']!='UNREACHABLE':
        return dict(status='UNSUPPORTED_FAILURE')
    q=failure['query'];slots={ctx.rc.fields['edge_ids'][s]:(u,ctx.rc.fields['dest_ranks'][s]) for u in range(len(ctx.context[2])) for s in range(ctx.rc.fields['row_offsets'][u],ctx.rc.fields['row_offsets'][u+1])}
    unions=defaultdict(set)
    for record in candidate['records']:
        union=unions[record['net_id']];union.add(record['source'])
        for eid in record['answer']['physical_edge_ids']:union.update(slots[eid])
    ledger=Counter(n for union in unions.values() for n in union)
    if dict(ledger)!={int(n):c for n,c in candidate['ledger'].items()}:
        raise ValueError('candidate ledger does not match NET ownership')
    forbidden=set()
    for query in ctx.context[5]:
        if (query['source'],query['sink'])==(q['source'],q['sink']):
            forbidden.update(restrictions.get(query['net_id'],()))
    witness=shortest_delay(ctx,q['source'],q['sink'],forbidden)
    if witness['minimum'] is None or witness['minimum']>budget:
        return dict(status='RELAXED_BUDGET_INFEASIBLE',query=q,witness=witness)
    blockers=[]
    for node in witness['path_nodes']:
        demand=ledger.get(node,0)-int(node in unions[q['net_id']])
        if demand>=ctx.rc.fields['capacities'][node]:
            owners=sorted(net for net,union in unions.items() if net!=q['net_id'] and node in union)
            if owners:blockers.append(dict(node=node,owners=owners))
    return dict(status='OBSERVED_CONFLICT' if blockers else 'NO_WITNESS_BLOCKER',query=q,witness=witness,blockers=blockers)

def detour_options(observation,restrictions,max_nets=16,max_exclusions=32):
    """Only direct conflicts from this observation generate new exclusions."""
    if observation['status']!='OBSERVED_CONFLICT':return []
    options=[]
    for blocker in observation['blockers']:
        for net in sorted({observation['query']['net_id'],*blocker['owners']}):
            proposed={k:set(v) for k,v in restrictions.items()}
            proposed.setdefault(net,set()).add(blocker['node'])
            if proposed==restrictions:continue
            if len(proposed)>max_nets or sum(map(len,proposed.values()))>max_exclusions:continue
            if proposed not in options:options.append(proposed)
    return options

def bounded_conflict_loop(initial,attempt,observe,allocate,max_attempts=8):
    """Callbacks run synchronously; never publish incomplete candidates.

    Allocation must return None for rejected options, or (score, allocation).
    Attempt returns a candidate. Restrictions accumulate only after allocation.
    """
    if type(max_attempts) is not int or max_attempts<1:raise ValueError('positive attempt bound required')
    restrictions={k:set(v) for k,v in initial.items()};trace=[]
    allocation_result=allocate(restrictions)
    if allocation_result is None:return dict(status='INITIAL_ALLOCATION_REJECTED',trace=trace)
    allocation=allocation_result[1]
    for iteration in range(max_attempts):
        candidate=attempt(restrictions,allocation)
        trace.append(dict(iteration=iteration,restrictions={k:sorted(v) for k,v in restrictions.items()},candidate=candidate))
        if candidate.get('failure') is None and candidate['completed_connections']==candidate['required_connections']:
            return dict(status='COMPLETE_CANDIDATE',trace=trace,candidate=candidate)
        if iteration+1==max_attempts:break
        observation=observe(candidate,restrictions,allocation);trace[-1]['observation']=observation
        options=detour_options(observation,restrictions);evaluated=[];accepted=[]
        for order,option in enumerate(options):
            result=allocate(option);evaluated.append(dict(restrictions={k:sorted(v) for k,v in option.items()},accepted=result is not None))
            if result is not None:accepted.append((result[0],order,option,result[1]))
        trace[-1]['options']=evaluated
        if not accepted:return dict(status='NO_ACCEPTED_DETOUR',trace=trace,candidate=candidate)
        _,_,restrictions,allocation=min(accepted,key=lambda x:(x[0],x[1]))
    return dict(status='ATTEMPT_LIMIT',trace=trace,candidate=candidate)
