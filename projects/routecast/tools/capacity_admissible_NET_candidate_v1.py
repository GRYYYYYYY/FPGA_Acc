"""Read-only whole-NET candidate; caller must apply original objective/overflow guards."""
from capacity_admissible_tree_v1 import CapacityMask,Graph
from criticality_retained_net_primary_v1 import route

def propose(original,fields,queries,old_records,criticalities,prices,ledger,edge_slots,max_labels=10000):
 old_nodes=set();old={r['connection_id']:r for r in old_records}
 for r in old_records:
  u=r['source'];old_nodes.add(u)
  for eid in r['answer']['physical_edge_ids']:
   edge=edge_slots[eid]
   if not original.offsets[u]<=edge<original.offsets[u+1]:raise ValueError('old path chain')
   u=original.dest[edge];old_nodes.add(u)
  if u!=r['sink']:raise ValueError('old path endpoint')
 mask=CapacityMask(fields['capacities'],ledger,old_nodes);graph=Graph(original,mask,max_labels)
 result=route(graph,queries,old_records,criticalities,prices,fields['edge_ids'],ledger,fields['capacities'],edge_slots)
 meta=dict(status='COMPLETE' if result['complete'] else 'NO_COMPLETE_CANDIDATE',old_owner_nodes=len(old_nodes),blocked_new_nodes=len(mask.blocked),max_labels=max_labels,retained_connection_ids=result['retained_connection_ids'],search_calls=result['search_calls'],first_failed_connection_id=result['first_failed_connection_id'],search_events=graph.events)
 if not result['complete']:return None,meta
 attempts={x['connection_id']:x['physical_edge_ids'] for x in result['attempts']};candidate=[];new_nodes=set()
 for q in queries:
  cid=q['connection_id'];u=q['source'];delay=original.initial[u];new_nodes.add(u);path=attempts[cid]
  if path is None:raise RuntimeError('complete candidate missing path')
  for eid in path:
   edge=edge_slots[eid];v=original.dest[edge]
   if not original.offsets[u]<=edge<original.offsets[u+1] or not mask[v]:raise RuntimeError('invalid masked candidate')
   delay+=original.inc[edge];new_nodes.add(v);u=v
  if u!=q['sink'] or delay>old[cid]['budget_integer']:raise RuntimeError('candidate budget/endpoint')
  candidate.append(dict(old[cid],answer=dict(status='FOUND',physical_edge_ids=path,delay=delay)))
 updates={n:ledger.get(n,0)-1 for n in old_nodes-new_nodes};updates.update({n:ledger.get(n,0)+1 for n in new_nodes-old_nodes})
 delta=sum(max(0,v-fields['capacities'][n])-max(0,ledger.get(n,0)-fields['capacities'][n]) for n,v in updates.items())
 if delta>0:raise RuntimeError('hard mask overflow invariant violated')
 meta['prospective_overflow_delta']=delta
 return candidate,meta
