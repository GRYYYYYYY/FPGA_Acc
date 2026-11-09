"""Bounded joint NET-group routing; caller owns transaction and cache lifecycle."""
from observer_state_clone_v2 import clone_state,clone_states
import copy,time,heapq
from pending_owner_joint_repair_v3 import constrained_witness
from collections import Counter,defaultdict,deque
from tree_floor_pareto_affected_seed_v13 import predict,EdgeSlotContext,SeedContext

def joint_route(fields,rc,groups,floors,kept,spans,penalty,global_required,remaining_cache=None,max_joint_nodes=32,deadline=None,observer=None,max_labels=10000,frontier="bfs",reuse_groups=False):
 if frontier not in ('bfs','dfs','parent_conflicts'):raise ValueError('unsupported frontier')
 if type(max_joint_nodes) is not int or max_joint_nodes<1:raise ValueError('positive joint-node limit required')
 if type(global_required) is not int or global_required<0:raise ValueError('global required count required')
 kept=copy.deepcopy(list(kept));groups=copy.deepcopy(groups);floors=dict(floors);spans=tuple(spans);memo={};requests=computations=reuses=0;kept_ids={r['connection_id'] for r in kept};query_ids=[]
 if len(kept_ids)!=len(kept):raise ValueError('duplicate kept identities')
 if not groups or any(not qs or any(q['net_id']!=net for q in qs) for net,qs in groups.items()):raise ValueError('nonempty single-NET groups required')
 for qs in groups.values():query_ids.extend(q['connection_id'] for q in qs)
 if len(set(query_ids))!=len(query_ids) or kept_ids.intersection(query_ids):raise ValueError('duplicate joint query identities')
 expected=kept_ids|set(query_ids)
 if len(expected)>global_required:raise ValueError('joint scope exceeds global required')
 edge_context=EdgeSlotContext(fields) if type(fields['edge_ids']) is tuple else None
 seed_context=SeedContext(fields,rc,kept,edge_context) if edge_context is not None and hasattr(rc,'arcs') else None
 nets=sorted(groups);slots=edge_context.slots(fields) if edge_context is not None else {e:s for s,e in enumerate(fields['edge_ids'])};queue=[(0,0,0,frozenset())] if frontier=='parent_conflicts' else deque([frozenset()]);serial=0;seen={frozenset()};branches=[];solution=None;owner_memo={};kept_owners=defaultdict(set)
 for r in kept:kept_owners[r['net_id']].add(r['source']);kept_owners[r['net_id']].update(fields['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
 cores=[];kept_counts=Counter(n for own in kept_owners.values() for n in own)
 while queue and len(branches)<max_joint_nodes and (deadline is None or time.perf_counter()<deadline):
  constraints=heapq.heappop(queue)[3] if frontier=='parent_conflicts' else queue.popleft();states={};index=len(branches)
  dominated=next((c for c in cores if c['constraints']<=constraints),None)
  if dominated is not None:
   entry=dict(index=index,constraints=sorted(constraints),failures={},status='PRUNED_ORDINARY_CORE',core_branch=dominated['branch'])
   branches.append(entry)
   if observer is not None:observer(copy.deepcopy(entry),{},None)
   continue
  for net in nets:
   requests+=1;forbidden=frozenset(n for owner,n in constraints if owner==net);key=(net,forbidden);was_reused=reuse_groups and key in memo
   if reuse_groups and key in memo:states[net]=memo[key];reuses+=1
   else:
    states[net]=predict(fields,rc,groups[net],floors,seed_records=kept if seed_context is None else (),seed_context=seed_context,spans=spans,penalty=penalty,remaining_cache=remaining_cache,forbidden_by_net={net:forbidden},deadline=deadline,max_labels=max_labels,edge_context=edge_context);computations+=1
    if reuse_groups and (states[net]['failure'] is None or states[net]['failure']['status']!='DEADLINE'):memo[key]=states[net]
   if not was_reused:
    own=set()
    for rec in states[net]['records']:
     if rec['net_id']==net:own.add(rec['source']);own.update(fields['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
    owner_memo[key]=frozenset(own)
  entry=dict(index=index,constraints=sorted(constraints),failures={str(net):state['failure'] for net,state in states.items()})
  if any(s['failure'] is not None for s in states.values()):entry['status']='LOW_LEVEL_FAILED'
  else:
   records={r['connection_id']:r for r in kept}
   for state in states.values():
    for r in state['records']:
     if r['connection_id'] in records:assert records[r['connection_id']]==r
     records[r['connection_id']]=r
   assert set(records)==expected
   owners=defaultdict(set,{net:set(own) for net,own in kept_owners.items()})
   for net in nets:
    key=(net,frozenset(n for owner,n in constraints if owner==net));owners[net].update(owner_memo[key])
   ledger=Counter(n for own in owners.values() for n in own);conflicts=sorted(n for n,count in ledger.items() if count>fields['capacities'][n]);entry['conflict_count']=len(conflicts)
   if not conflicts:
    solution=dict(records=sorted(records.values(),key=lambda r:r['connection_id']),ledger=dict(ledger),completed_connections=len(records),required_connections=global_required,failure=None,scope='LOCAL_JOINT_BATCH_ONLY_GLOBAL_PARTIAL');entry['status']='FOUND_JOINT_BATCH'
   else:
    node=min(conflicts,key=lambda n:(-(ledger[n]-fields['capacities'][n]),-sum(n in owners[net] for net in nets),n));participants=[net for net in nets if node in owners[net]];assert len(participants)>=2;entry.update(status='SPLIT',conflict_node=node,conflict_excess=ledger[node]-fields['capacities'][node],conflict_participants=participants,conflict_policy='maximum excess, maximum joint owners, minimum node id')
    for net in (participants if frontier=='bfs' else list(reversed(participants))):
     child=constraints|{(net,node)}
     if child not in seen:
      seen.add(child)
      if frontier=='parent_conflicts':
       serial+=1;heapq.heappush(queue,(len(conflicts),len(child),serial,child))
      elif frontier=='bfs':queue.append(child)
      else:queue.appendleft(child)
  for net,state in states.items():
   failure=state['failure']
   if failure is None or failure['status']!='NO_BUDGET_CAPACITY_PATH':continue
   bans=frozenset(n for owner,n in constraints if owner==net)
   blocked={n for n,c in kept_counts.items() if c-(n in kept_owners.get(net,set()))>=fields['capacities'][n]}
   try:witness=constrained_witness(fields,rc,failure['query'],bans|blocked,deadline)
   except TimeoutError:continue
   if witness is None or witness['minimum_integer']>failure['budget_integer']:
    core=frozenset((net,n) for n in bans);cores.append(dict(constraints=core,branch=index))
    entry.setdefault('ordinary_cores',[]).append(dict(net=net,query=failure['query'],budget=failure['budget_integer'],bans=sorted(bans),minimum_integer=None if witness is None else witness['minimum_integer']))
  branches.append(entry)
  if observer is not None:observer(copy.deepcopy(entry),clone_states(states),clone_state(solution))
  if solution is not None:break
 status='FOUND_JOINT_BATCH' if solution is not None else 'DEADLINE' if deadline is not None and time.perf_counter()>=deadline else 'JOINT_NODE_LIMIT' if queue else 'SEARCH_EXHAUSTED'
 return dict(status=status,solution=solution,branches=branches,remaining_branches=len(queue),joint_query_ids=sorted(query_ids),low_level_requests=requests,low_level_computations=computations,low_level_reuses=reuses,memo_entries=len(memo),memo_record_count=sum(len(state['records']) for state in memo.values()),scope='Bounded low-level greedy tree routing, not general complete multi-agent solver. Cache finalize and commit/rollback belong to caller.')
