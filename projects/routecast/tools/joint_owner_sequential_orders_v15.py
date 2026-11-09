"""Whole-NET prioritized capacity-aware reinsert, bounded cyclic/reversed orders."""
import copy,time
from tree_floor_pareto_affected_seed_v13 import predict
from observer_state_clone_v2 import clone_state,clone_states

def joint_route(fields,rc,groups,floors,kept,spans,penalty,global_required,remaining_cache=None,max_joint_nodes=32,deadline=None,observer=None,max_labels=10000,frontier='bfs',reuse_groups=False):
 nets=sorted(groups);orders=[]
 for base in (nets,list(reversed(nets))):
  for offset in range(len(base)):
   order=tuple(base[offset:]+base[:offset])
   if order not in orders:orders.append(order)
 expected={r['connection_id'] for r in kept}|{q['connection_id'] for qs in groups.values() for q in qs};assert len(expected)==len(kept)+sum(len(qs) for qs in groups.values());branches=[];solution=None
 for order in orders[:max_joint_nodes]:
  if deadline is not None and time.perf_counter()>=deadline:break
  seed=copy.deepcopy(kept);states={};entry=dict(index=len(branches),constraints=[],net_order=list(order),failures={})
  for net in order:
   state=predict(fields,rc,groups[net],floors,seed_records=seed,spans=spans,penalty=penalty,remaining_cache=remaining_cache,deadline=deadline,max_labels=max_labels);states[net]=state;entry['failures'][str(net)]=state['failure']
   if state['failure'] is not None:break
   previous={r['connection_id']:r for r in state['records']};assert all(previous[r['connection_id']]==r for r in seed);seed=state['records']
  if all(net in states and states[net]['failure'] is None for net in order):
   assert {r['connection_id'] for r in seed}==expected;last=states[order[-1]];solution=dict(records=sorted(seed,key=lambda r:r['connection_id']),ledger=last['ledger'],completed_connections=len(seed),required_connections=global_required,failure=None,scope='LOCAL_PRIORITIZED_WHOLE_NET_BATCH');entry['status']='FOUND_JOINT_BATCH';entry['conflict_count']=0
  else:entry['status']='LOW_LEVEL_FAILED'
  branches.append(entry)
  if observer is not None:observer(copy.deepcopy(entry),clone_states(states),clone_state(solution))
  if solution is not None:break
 status='FOUND_JOINT_BATCH' if solution is not None else 'DEADLINE' if deadline is not None and time.perf_counter()>=deadline else 'SEARCH_EXHAUSTED' if len(branches)==len(orders) else 'JOINT_NODE_LIMIT'
 return dict(status=status,solution=solution,branches=branches,remaining_branches=len(orders)-len(branches),scope='Bounded greedy prioritized full-NET orders, not global complete solver.')
