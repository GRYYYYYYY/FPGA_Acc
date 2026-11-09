"""Bounded greedy continuation with all-or-nothing owner-reinsert batches."""
import heapq
from collections import defaultdict,Counter
from pending_owner_prefix_v1 import select
from joint_owner_edge_context_v5 import joint_route
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
  event=dict(index=attempts,query=q,selection=selection,joint_status=result['status'],initial_release_net_ids=initial_release,sequential_failure=sequential_failure,repair_status=None if repair_result is None else repair_result['status'],repair_attempts=[] if repair_result is None else repair_result['attempts'],blocked_nodes=blocked,released_net_ids=release,removed_connection_ids=[r['connection_id'] for r in removed],committed=commit,batch_failure=working['failure'],before_records=accepted,working_records=working['records'],before_ledger=state['ledger'],working_ledger=working['ledger']);events.append(event)
  if observer:observer(event)
  if not commit:return state,events,'BATCH_ROLLBACK'
  assert {r['connection_id'] for r in working['records']}=={r['connection_id'] for r in accepted}|set(selection['requested_connection_ids'])
  accepted=working['records']
