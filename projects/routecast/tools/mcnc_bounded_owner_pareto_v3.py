"""Bounded greedy continuation with all-or-nothing owner-reinsert batches."""
import heapq
from collections import defaultdict,Counter
from tree_floor_pareto_predictor_v4 import predict as base_predict

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

def sequence(f,rc,queries,floors,max_batches=8,max_owner_nets=4,deadline=None,observer=None,spans=None,penalty=0):
 def predict(*args,**kwargs):return base_predict(*args,**kwargs,spans=spans,penalty=penalty,max_labels=10000)
 ordered=sorted(queries,key=lambda q:(q['net_id'],q['connection_id']));accepted=[];events=[];eid_slot={e:s for s,e in enumerate(f['edge_ids'])};attempts=0
 def scoped(state):
  state['required_connections']=len(queries);state['pending_connection_ids']=sorted({q['connection_id'] for q in queries}-{r['connection_id'] for r in state['records']});state['status']='COMPLETE_DIAGNOSTIC' if not state['pending_connection_ids'] else 'INCOMPLETE_NOT_PUBLISHABLE';return state
 while True:
  done={r['connection_id'] for r in accepted};pending=[q for q in ordered if q['connection_id'] not in done];state=scoped(predict(f,rc,pending,floors,seed_records=accepted,deadline=deadline));accepted=state['records']
  if state['failure'] is None:return state,events,'COMPLETE'
  if state['failure']['status']!='NO_BUDGET_CAPACITY_PATH':return state,events,state['failure']['status']
  if attempts>=max_batches:return state,events,'BATCH_LIMIT'
  q=state['failure']['query'];witness=minimum_witness(f,rc,q)
  if witness is None:return state,events,'INPUT_UNREACHABLE'
  owners=defaultdict(set)
  for r in accepted:
   owners[r['net_id']].add(r['source']);owners[r['net_id']].update(f['dest_ranks'][eid_slot[e]] for e in r['answer']['physical_edge_ids'])
  other=Counter(n for net,ns in owners.items() if net!=q['net_id'] for n in ns);nodes={q['source']}|{f['dest_ranks'][eid_slot[e]] for e in witness};blocked=sorted(n for n in nodes if other.get(n,0)>=f['capacities'][n]);release=sorted(net for net,ns in owners.items() if net!=q['net_id'] and any(n in ns for n in blocked))
  if not release:return state,events,'NO_WITNESS_OWNER'
  if len(release)>max_owner_nets:return state,events,'OWNER_LIMIT'
  kept=[r for r in accepted if r['net_id'] not in release];removed=[r for r in accepted if r['net_id'] in release];batch=[q]+[{k:r[k] for k in ('connection_id','net_id','source','sink')} for r in sorted(removed,key=lambda r:(r['net_id'],r['connection_id']))];working=predict(f,rc,batch,floors,seed_records=kept,deadline=deadline);commit=working['failure'] is None;attempts+=1
  event=dict(index=attempts,query=q,blocked_nodes=blocked,released_net_ids=release,removed_connection_ids=[r['connection_id'] for r in removed],committed=commit,batch_failure=working['failure'],before_records=accepted,working_records=working['records'],before_ledger=state['ledger'],working_ledger=working['ledger']);events.append(event)
  if observer:observer(event)
  if not commit:return state,events,'BATCH_ROLLBACK'
  assert {r['connection_id'] for r in working['records']}=={r['connection_id'] for r in accepted}|{q['connection_id']}
  accepted=working['records']
