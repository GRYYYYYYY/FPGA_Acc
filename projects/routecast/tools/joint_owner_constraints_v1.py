"""Bounded joint NET-group routing; caller owns transaction and cache lifecycle."""
import copy,time
from collections import Counter,defaultdict,deque
from tree_floor_pareto_constraints_predictor_v7 import predict

def joint_route(fields,rc,groups,floors,kept,spans,penalty,global_required,remaining_cache=None,max_joint_nodes=32,deadline=None,observer=None,max_labels=10000):
 if type(max_joint_nodes) is not int or max_joint_nodes<1:raise ValueError('positive joint-node limit required')
 if type(global_required) is not int or global_required<0:raise ValueError('global required count required')
 kept=copy.deepcopy(list(kept));groups=copy.deepcopy(groups);kept_ids={r['connection_id'] for r in kept};query_ids=[]
 if len(kept_ids)!=len(kept):raise ValueError('duplicate kept identities')
 if not groups or any(not qs or any(q['net_id']!=net for q in qs) for net,qs in groups.items()):raise ValueError('nonempty single-NET groups required')
 for qs in groups.values():query_ids.extend(q['connection_id'] for q in qs)
 if len(set(query_ids))!=len(query_ids) or kept_ids.intersection(query_ids):raise ValueError('duplicate joint query identities')
 expected=kept_ids|set(query_ids)
 if len(expected)>global_required:raise ValueError('joint scope exceeds global required')
 nets=sorted(groups);slots={e:s for s,e in enumerate(fields['edge_ids'])};queue=deque([frozenset()]);seen={frozenset()};branches=[];solution=None
 while queue and len(branches)<max_joint_nodes and (deadline is None or time.perf_counter()<deadline):
  constraints=queue.popleft();states={};index=len(branches)
  for net in nets:
   states[net]=predict(fields,rc,groups[net],floors,seed_records=kept,spans=spans,penalty=penalty,remaining_cache=remaining_cache,forbidden_by_net={net:frozenset(n for owner,n in constraints if owner==net)},deadline=deadline,max_labels=max_labels)
  entry=dict(index=index,constraints=sorted(constraints),failures={str(net):state['failure'] for net,state in states.items()})
  if any(s['failure'] is not None for s in states.values()):entry['status']='LOW_LEVEL_FAILED'
  else:
   records={r['connection_id']:r for r in kept}
   for state in states.values():
    for r in state['records']:
     if r['connection_id'] in records:assert records[r['connection_id']]==r
     records[r['connection_id']]=r
   assert set(records)==expected
   owners=defaultdict(set)
   for r in records.values():owners[r['net_id']].add(r['source']);owners[r['net_id']].update(fields['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
   ledger=Counter(n for own in owners.values() for n in own);conflicts=sorted(n for n,count in ledger.items() if count>fields['capacities'][n]);entry['conflict_count']=len(conflicts)
   if not conflicts:
    solution=dict(records=sorted(records.values(),key=lambda r:r['connection_id']),ledger=dict(ledger),completed_connections=len(records),required_connections=global_required,failure=None,scope='LOCAL_JOINT_BATCH_ONLY_GLOBAL_PARTIAL');entry['status']='FOUND_JOINT_BATCH'
   else:
    node=conflicts[0];participants=[net for net in nets if node in owners[net]];assert len(participants)>=2;entry.update(status='SPLIT',conflict_node=node)
    for net in participants:
     child=constraints|{(net,node)}
     if child not in seen:seen.add(child);queue.append(child)
  branches.append(entry)
  if observer is not None:observer(copy.deepcopy(entry),copy.deepcopy(states),copy.deepcopy(solution))
  if solution is not None:break
 status='FOUND_JOINT_BATCH' if solution is not None else 'DEADLINE' if deadline is not None and time.perf_counter()>=deadline else 'JOINT_NODE_LIMIT' if queue else 'SEARCH_EXHAUSTED'
 return dict(status=status,solution=solution,branches=branches,remaining_branches=len(queue),joint_query_ids=sorted(query_ids),scope='Bounded low-level greedy tree routing, not general complete multi-agent solver. Cache finalize and commit/rollback belong to caller.')
