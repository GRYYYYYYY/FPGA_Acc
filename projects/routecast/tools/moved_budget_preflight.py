"""Read-only local budget feasibility probe; restores incumbent endpoint binding."""
import heapq

def check(ctx,endpoint_path,budgets):
 if any(type(c)is not int or type(b)is not int or c<0 or b<0 for c,b in budgets.items()):raise ValueError('nonnegative integer connection budgets required')
 original_context=ctx.context;original_metadata=ctx.endpoint_metadata
 try:
  affected=ctx.bind_endpoints(endpoint_path);cohort=set(affected['affected_complete_net_connection_ids']);queries=[q for q in ctx.context[5]if q['connection_id']in cohort and q['connection_id']in budgets];f=ctx.rc.fields;observations=[]
  if set(budgets)-{q['connection_id']for q in ctx.context[5]}:raise ValueError('unknown budget connection')
  for q in queries:
   source=q['source'];sink=q['sink'];budget=budgets[q['connection_id']];initial=ctx.rc.initial(source);dist={source:initial}if f['capacities'][source]>0 and initial<=budget else {};heap=[(initial,source)]if dist else [];expanded=0;minimum=None
   while heap:
    delay,node=heapq.heappop(heap)
    if dist[node]!=delay:continue
    expanded+=1
    if node==sink:minimum=delay;break
    for slot in range(f['row_offsets'][node],f['row_offsets'][node+1]):
     dest=f['dest_ranks'][slot]
     if not f['capacities'][dest]:continue
     nd=delay+ctx.rc.increments[slot]
     if nd<=budget and(dest not in dist or nd<dist[dest]):dist[dest]=nd;heapq.heappush(heap,(nd,dest))
   observations.append(dict(query=q,budget_units=budget,minimum_units=minimum,feasible=minimum is not None,expanded=expanded,discovered=len(dist)))
   if minimum is None:break
  return dict(affected=affected,budgeted_affected_connections=len(queries),observations=observations,status='REJECT_BUDGET_CANDIDATE_USE_NATIVE_COLD'if observations and not observations[-1]['feasible']else'BUDGET_PREFLIGHT_PASS_NOT_ROUTE_PROOF')
 finally:
  ctx.context=original_context;ctx.endpoint_metadata=original_metadata
