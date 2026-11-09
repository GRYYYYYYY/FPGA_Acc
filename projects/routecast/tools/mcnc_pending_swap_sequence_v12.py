"""Bounded greedy continuation with all-or-nothing owner-reinsert batches."""
import heapq
from collections import defaultdict,Counter
from pending_owner_prefix_v1 import select
from joint_owner_seed_context_v7 import joint_route
from pending_owner_joint_repair_v3 import repair
from pending_owner_swap_proposals_v1 import propose
import time
from tree_floor_pareto_cache_predictor_v6 import predict as base_predict

def minimum_witness(f,rc,q):
 src,sink=q['source'],q['sink'];dist={src:rc.initial(src)};back={};heap=[(dist[src],src)]
 while heap:
  d,u=heapq.heappop(heap)
  if d!=dist[u]:continue
  if u==sink:
   path=[];node=sink
   while node!=src:node,eid=back[node];path.append(eid)
   path.reverse();assert rc.path(src,sink,path)==d;return path
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][s]
   if f['capacities'][v]<=0:continue
   nd=d+rc.increments[s]
   if v not in dist or nd<dist[v]:dist[v]=nd;back[v]=(u,f['edge_ids'][s]);heapq.heappush(heap,(nd,v))
 return None

def sequence(f,rc,queries,floors,max_batches=8,max_owner_nets=4,deadline=None,observer=None,spans=None,penalty=0,remaining_cache=None,repair_observer=None):
 def predict(*args,**kwargs):return base_predict(*args,**kwargs,spans=spans,penalty=penalty,max_labels=10000,remaining_cache=remaining_cache)
 ordered=sorted(queries,key=lambda q:(q['net_id'],q['connection_id']));accepted=[];events=[];eid_slot={e:s for s,e in enumerate(f['edge_ids'])};attempts=0
 def scoped(state):
  state['required_connections']=len(queries);state['pending_connection_ids']=sorted({q['connection_id'] for q in queries}-{r['connection_id'] for r in state['records']});state['status']='COMPLETE_DIAGNOSTIC' if not state['pending_connection_ids'] else 'INCOMPLETE_NOT_PUBLISHABLE';return state
 while True:
  done={r['connection_id'] for r in accepted};pending=[q for q in ordered if q['connection_id'] not in done];state=scoped(predict(f,rc,pending,floors,seed_records=accepted,deadline=deadline));accepted=state['records']
  if state['failure'] is None:return state,events,'COMPLETE'
  if state['failure']['status']!='NO_BUDGET_CAPACITY_PATH':return state,events,state['failure']['status']
  if attempts>=max_batches:return state,events,'BATCH_LIMIT'
  q=state['failure']['query'];pending=[x for x in ordered if x['connection_id'] not in {r['connection_id'] for r in accepted}]
  selection=select(f,rc,accepted,pending,max_owner_nets=max_owner_nets,max_queries=16,deadline=deadline)
  if not selection['queries']:return state,events,selection['stop']
  release=selection['released_net_ids'];blocked=sorted({n for x in selection['witness_evidence'] if x['selected'] for n in x['blocked_nodes']});kept=[r for r in accepted if r['net_id'] not in release];removed=[r for r in accepted if r['net_id'] in release];groups=defaultdict(list)
  for x in selection['queries']:groups[x['net_id']].append(x)
  for r in sorted(removed,key=lambda r:(r['net_id'],r['connection_id'])):groups[r['net_id']].append({k:r[k] for k in ('connection_id','net_id','source','sink')})
  attempts+=1
  def trace(branch,states,solution):
   if repair_observer is not None:repair_observer(attempts,1,release,branch,states,solution)
  result=joint_route(f,rc,dict(groups),floors,kept,spans,penalty,len(queries),remaining_cache=remaining_cache,max_joint_nodes=64,deadline=deadline,observer=trace,frontier='dfs',reuse_groups=True)
  commit=result['solution'] is not None;working=result['solution'] if commit else state;sequential_failure=None;initial_release=list(release);repair_result=dict(status=result['status'],attempts=result['branches'] if 'branches' in result else [])
  owner_repair=None
  if not commit and result['status']!='DEADLINE':
   def expansion_trace(attempt_index,release_nets,branch,states,solution):
    if repair_observer is not None:repair_observer(attempts,attempt_index+2,release_nets,branch,states,solution)
   owner_repair=repair(f,rc,accepted,selection['queries'],release,floors,spans,penalty,len(queries),remaining_cache=remaining_cache,max_owner_nets=max_owner_nets,max_release_attempts=4,max_joint_nodes=64,deadline=deadline,observer=expansion_trace)
   if owner_repair['solution'] is not None:
    working=owner_repair['solution'];commit=True;release=owner_repair['released_net_ids'];removed=[r for r in accepted if r['net_id'] in release]
  owner_swap=None
  if not commit and result['status']!='DEADLINE' and owner_repair is not None and (deadline is None or time.perf_counter()<deadline):
   branches=[branch for attempt in owner_repair['attempts'] for branch in attempt['branches']]
   try:
    proposals=propose(f,rc,accepted,release,branches,deadline,max_domains=4,max_checks=32,max_candidates=4)
    owner_swap=dict(screening=proposals,attempts=[],status='SWAP_EXHAUSTED')
    offset=2+len(owner_repair['attempts'])
    for index,candidate in enumerate(proposals['proposed']):
     candidate_set=set(candidate);swap_kept=[r for r in accepted if r['net_id'] not in candidate_set];swap_removed=[r for r in accepted if r['net_id'] in candidate_set];swap_groups=defaultdict(list)
     for query in selection['queries']:swap_groups[query['net_id']].append(query)
     for rec in sorted(swap_removed,key=lambda r:(r['net_id'],r['connection_id'])):swap_groups[rec['net_id']].append({k:rec[k] for k in ('connection_id','net_id','source','sink')})
     def swap_trace(branch,states,solution):
      if repair_observer is not None:repair_observer(attempts,offset+index,candidate,branch,states,solution)
     swap=joint_route(f,rc,dict(swap_groups),floors,swap_kept,spans,penalty,len(queries),remaining_cache=remaining_cache,max_joint_nodes=64,deadline=deadline,observer=swap_trace,frontier='dfs',reuse_groups=True)
     owner_swap['attempts'].append(dict(index=index,released_net_ids=candidate,joint_status=swap['status'],branches=swap['branches']))
     if swap['solution'] is not None:working=swap['solution'];commit=True;release=candidate;removed=swap_removed;owner_swap['status']='FOUND_JOINT_BATCH';break
     if swap['status']=='DEADLINE':owner_swap['status']='DEADLINE';break
   except TimeoutError:owner_swap=dict(status='DEADLINE',screening=None,attempts=[])
  event=dict(index=attempts,query=q,owner_swap=owner_swap,owner_repair=None if owner_repair is None else {k:v for k,v in owner_repair.items() if k!='solution'},selection=selection,joint_status=result['status'],initial_release_net_ids=initial_release,sequential_failure=sequential_failure,repair_status=None if repair_result is None else repair_result['status'],repair_attempts=[] if repair_result is None else repair_result['attempts'],blocked_nodes=blocked,released_net_ids=release,removed_connection_ids=[r['connection_id'] for r in removed],committed=commit,batch_failure=working['failure'],before_records=accepted,working_records=working['records'],before_ledger=state['ledger'],working_ledger=working['ledger']);events.append(event)
  if observer:observer(event)
  if not commit:return state,events,'BATCH_ROLLBACK'
  assert {r['connection_id'] for r in working['records']}=={r['connection_id'] for r in accepted}|set(selection['requested_connection_ids'])
  accepted=working['records']
