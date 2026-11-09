"""Sequential joint exact-delay prediction through a persistent graph context."""
import heapq
from capacity_local_demand import CapacityLocalDemand,resident_query
from collections import Counter,defaultdict

def predict_joint(ctx,max_labels=10000,fallback_limit=64,state=None):
 if type(max_labels) is not int or max_labels<1:raise ValueError('positive label bound required')
 if type(fallback_limit) is not int or fallback_limit<0:raise ValueError('nonnegative fallback bound required')
 graph,digest,nodes,f,rc,queries=ctx.context
 ctx.reset()
 if fallback_limit!=0:raise ValueError("resident initial prediction requires no fallback")
 local=CapacityLocalDemand(ctx.native);dirty=set()
 if state is not None:
  if state.ctx is not ctx or state.records or state.ledger:raise ValueError('initial prediction requires empty matching ledger')
 budget=rc.scale//10**9;slots={f['edge_ids'][s]:(u,f['dest_ranks'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};unions=defaultdict(set);ledger=Counter();parents=defaultdict(dict);records=[];attempts=[];fallbacks=0;failure=None
 if state is not None:slots,unions,ledger,parents=state.slots,state.unions,state.ledger,state.parents
 
 def fallback(q,other):
  src,sink=q['source'],q['sink']
  if other.get(src,0)>=f['capacities'][src]:return {'status':'DISCONNECTED'}
  dist={src:rc.initial(src)};back={};heap=[(dist[src],src)]
  while heap:
   delay,u=heapq.heappop(heap)
   if delay!=dist[u]:continue
   if u==sink:
    path=[];node=sink
    while node!=src:node,eid=back[node];path.append(eid)
    return {'status':'FOUND' if delay<=budget else 'OVER_BUDGET','physical_edge_ids':path[::-1],'delay':delay}
   for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    dst=f['dest_ranks'][s]
    if other.get(dst,0)>=f['capacities'][dst]:continue
    nd=delay+rc.increments[s]
    if dst not in dist or nd<dist[dst]:dist[dst]=nd;back[dst]=(u,f['edge_ids'][s]);heapq.heappush(heap,(nd,dst))
  return {'status':'DISCONNECTED'}
 for q in sorted(queries,key=lambda q:(q['net_id'],q['connection_id'])):
  net=q['net_id'];ctx.set_wire_owner_union(unions[net]);answer=resident_query(ctx,local,ledger,unions[net],dirty,q['source'],q['sink'],budget,max_labels=max_labels);other=local.values;mode='NATIVE_DELAY_COST';attempt={'query':q,'native_answer':answer,'wire_owner_union':sorted(unions[net])}
  if answer['status'] in ('LABEL_LIMIT','UNREACHABLE') and fallbacks<fallback_limit:
   fallbacks+=1;answer=fallback(q,other);attempt['fallback_answer']=answer;mode='MINIMUM_DELAY_FALLBACK'
  attempts.append(attempt)
  if answer['status']!='FOUND':failure={'query':q,'status':answer['status']};break
  node=q['source'];used={node};incoming={}
  for eid in answer['physical_edge_ids']:u,node2=slots[eid];assert node==u;node=node2;used.add(node);incoming[node]=(u,eid)
  assert node==q['sink'] and all(other.get(n,0)<f['capacities'][n] for n in used)
  conflicts=[n for n,p in incoming.items() if n in parents[net] and parents[net][n]!=p]
  if conflicts:failure={'query':q,'status':'MULTI_PARENT_REJECTED','nodes':conflicts};break
  parents[net].update(incoming);dirty.update(used-unions[net]);ledger.update(used-unions[net]);unions[net].update(used);records.append({**q,'mode':mode,'answer':answer})
 if state is not None:state.records.update({r['connection_id']:r for r in records})
 return {'status':'COMPLETE_DIAGNOSTIC' if failure is None else 'INCOMPLETE_NOT_PUBLISHABLE','records':records,'attempts':attempts,'failure':failure,'completed_connections':len(records),'required_connections':len(queries),'fallbacks':fallbacks,'ledger':dict(ledger),'graph_sha256':digest,'scale':rc.scale,'budget_integer':budget}
