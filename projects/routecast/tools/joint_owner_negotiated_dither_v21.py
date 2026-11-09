"""Bounded independent whole-NET proposals with negotiated capacity history."""
import copy,time,hashlib
from collections import Counter,defaultdict
from tree_floor_pareto_affected_seed_v13 import predict
from observer_state_clone_v2 import clone_state,clone_states

def joint_route(fields,rc,groups,floors,kept,spans,penalty,global_required,remaining_cache=None,max_joint_nodes=32,deadline=None,observer=None,max_labels=10000,frontier=None,reuse_groups=False,original_records=None):
 slots={e:i for i,e in enumerate(fields['edge_ids'])};weight_cache={};history=Counter();branches=[];solution=None;nets=sorted(groups)
 expected={r['connection_id'] for r in kept}|{q['connection_id'] for qs in groups.values() for q in qs}
 assert len(expected)==len(kept)+sum(len(qs) for qs in groups.values())
 def ledger_of(records):
  owners=defaultdict(set)
  for rec in records:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(fields['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
  return Counter(n for own in owners.values() for n in own)
 for iteration in range(min(max_joint_nodes,32)):
  if deadline is not None and time.perf_counter()>=deadline:break
  weighted=[span+8*history[node] for node,span in enumerate(spans)];states={};entry=dict(index=iteration,constraints=[],failures={},history_price_sha256={});records={r['connection_id']:r for r in kept}
  for net in nets:
   weighted=list(spans)
   for node,count in history.items():
    key=(net,node)
    if key not in weight_cache:weight_cache[key]=8+hashlib.sha256(f'routecast-history-dither-v1:{net}:{node}'.encode()).digest()[0]%8
    weighted[node]+=count*weight_cache[key]
   entry['history_price_sha256'][str(net)]=hashlib.sha256(','.join(map(str,weighted)).encode()).hexdigest()
   state=predict(fields,rc,groups[net],floors,seed_records=kept,spans=weighted,penalty=penalty,remaining_cache=remaining_cache,deadline=deadline,max_labels=max_labels);states[net]=state;entry['failures'][str(net)]=state['failure']
   if state['failure'] is not None:break
   for rec in state['records']:
    if rec['connection_id'] in records:assert records[rec['connection_id']]==rec
    else:records[rec['connection_id']]=rec
  if len(states)==len(nets) and all(s['failure'] is None for s in states.values()):
   assert set(records)==expected;ledger=ledger_of(records.values());conflicts={node:count-fields['capacities'][node] for node,count in ledger.items() if count>fields['capacities'][node]};entry['overuse_by_node']={str(n):v for n,v in sorted(conflicts.items())};entry['conflict_count']=len(conflicts)
   if not conflicts:
    solution=dict(records=sorted(records.values(),key=lambda r:r['connection_id']),ledger=dict(ledger),completed_connections=len(records),required_connections=global_required,failure=None,scope='LOCAL_NEGOTIATED_WHOLE_NET_BATCH');entry['status']='FOUND_JOINT_BATCH'
   else:entry['status']='NEGOTIATED_OVERUSE';history.update(conflicts)
  else:entry['status']='LOW_LEVEL_FAILED'
  branches.append(entry)
  if observer is not None:observer(copy.deepcopy(entry),clone_states(states),clone_state(solution))
  if solution is not None or entry['status']=='LOW_LEVEL_FAILED':break
 status='FOUND_JOINT_BATCH' if solution is not None else 'DEADLINE' if deadline is not None and time.perf_counter()>=deadline else 'LOW_LEVEL_FAILED' if branches and branches[-1]['status']=='LOW_LEVEL_FAILED' else 'SEARCH_EXHAUSTED'
 return dict(status=status,solution=solution,branches=branches,remaining_branches=max(0,min(max_joint_nodes,32)-len(branches)),scope='At most32 negotiated whole-NET iterations, no global completeness.')
