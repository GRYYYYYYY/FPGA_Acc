"""Whole-NET prioritized capacity-aware reinsert, bounded cyclic/reversed orders."""
import copy,time,hashlib
from collections import Counter,defaultdict
from tree_floor_pareto_affected_seed_v13 import predict
from observer_state_clone_v2 import clone_state,clone_states

def joint_route(fields,rc,groups,floors,kept,spans,penalty,global_required,remaining_cache=None,max_joint_nodes=32,deadline=None,observer=None,max_labels=10000,frontier='bfs',reuse_groups=False,original_records=None):
 originals=defaultdict(list);slots={e:i for i,e in enumerate(fields['edge_ids'])}
 for rec in original_records or ():originals[rec['net_id']].append(rec)
 def ledger_of(records):
  owners=defaultdict(set)
  for rec in records:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(fields['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
  return dict(Counter(n for own in owners.values() for n in own))
 original_nodes={}
 for n,recs in originals.items():
  own=set()
  for rec in recs:own.add(rec['source']);own.update(fields['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
  original_nodes[n]=own
 nets=sorted(groups);targets=sorted(n for n in nets if {q['connection_id'] for q in groups[n]}!={r['connection_id'] for r in originals[n]});others=sorted(set(nets)-set(targets));orders=[]
 for index in range(64):
  ranked=sorted(others,key=lambda n:(hashlib.sha256(f'routecast-target-first-v1:{index}:{n}'.encode()).digest(),n));order=tuple(targets+ranked)
  if order not in orders:orders.append(order)
 expected={r['connection_id'] for r in kept}|{q['connection_id'] for qs in groups.values() for q in qs};assert len(expected)==len(kept)+sum(len(qs) for qs in groups.values());branches=[];solution=None
 for order in orders[:max_joint_nodes]:
  if deadline is not None and time.perf_counter()>=deadline:break
  seed=copy.deepcopy(kept);states={};entry=dict(index=len(branches),constraints=[],net_order=list(order),failures={})
  for net in order:
   warm=originals[net];warm_ids={r['connection_id'] for r in warm};query_ids={q['connection_id'] for q in groups[net]};candidate=seed+copy.deepcopy(warm);ledger=ledger_of(candidate) if warm_ids==query_ids else None
   if ledger is not None and all(c<=fields['capacities'][n] for n,c in ledger.items()):
    state=dict(records=candidate,ledger=ledger,failure=None,completed_connections=len(candidate),required_connections=global_required);entry.setdefault('warm_restored_nets',[]).append(net)
   else:
    future=order[order.index(net)+1:];pressure=Counter(n for owner in future for n in original_nodes.get(owner,()));weighted=[span+32*pressure[n] for n,span in enumerate(spans)];state=predict(fields,rc,groups[net],floors,seed_records=seed,spans=weighted,penalty=penalty,remaining_cache=remaining_cache,deadline=deadline,max_labels=max_labels);entry.setdefault('reservation_pressure_sha256',{})[str(net)]=hashlib.sha256(','.join(map(str,weighted)).encode()).hexdigest()
   states[net]=state;entry['failures'][str(net)]=state['failure']
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
