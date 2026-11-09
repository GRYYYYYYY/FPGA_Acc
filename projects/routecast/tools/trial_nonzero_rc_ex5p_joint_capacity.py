"""Bounded sequential joint union accounting with exact-delay feasibility fallback."""
import json,heapq,time
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_capacity_rc_search import NativeCapacityRC
root=Path(__file__).resolve().parents[1];ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json';v=json.loads((ep.parent/'verification.json').read_text());assert v['endpoint_sha256']==sha(ep);out=root/'experiments/nonzero_rc_ex5p_joint_capacity_2026-10-06';out.mkdir();(out/'protocol.json').write_text(json.dumps({'endpoint_sha256':sha(ep),'budget_ns':1,'max_labels':10000,'fallback_limit':64,'policy':'NETid/connectionid order, perNET union ledger, other=demand minus ownunion; unit-edge native first; LABEL_LIMIT/UNREACHABLE exact-delay Dijkstra fallback (max64); stop infeasible bound/disconnection/unsupported status or multiparent; no native path/timing reads','scope':'Bounded development policy on ex5p, incomplete retained states never published'},indent=2)+'\n');start=time.monotonic();graph,digest,nodes,f,rc,queries=load_endpoints(ep);native=NativeCapacityRC(rc);budget=rc.scale//10**9;slots={f['edge_ids'][s]:(u,f['dest_ranks'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};unions=defaultdict(set);ledger=Counter();parents=defaultdict(dict);records=[];attempts=[];fallbacks=0;failure=None

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
 net=q['net_id'];other=dict(ledger)
 for n in unions[net]:other[n]-=1
 other={n:value for n,value in other.items() if value};native.set_other(other);answer=native.query(q['source'],q['sink'],budget,max_labels=10000);mode='NATIVE_UNIT_COST';attempt={'query':q,'native_answer':answer}
 if answer['status'] in ('LABEL_LIMIT','UNREACHABLE') and fallbacks<64:
  fallbacks+=1;answer=fallback(q,other);attempt['fallback_answer']=answer;mode='MINIMUM_DELAY_FALLBACK'
 attempts.append(attempt)
 if answer['status']!='FOUND':failure={'query':q,'status':answer['status']};break
 node=q['source'];used={node};incoming={}
 for eid in answer['physical_edge_ids']:u,node2=slots[eid];assert node==u;node=node2;used.add(node);incoming[node]=(u,eid)
 assert node==q['sink'] and all(other.get(n,0)<f['capacities'][n] for n in used)
 conflicts=[n for n,p in incoming.items() if n in parents[net] and parents[net][n]!=p]
 if conflicts:failure={'query':q,'status':'MULTI_PARENT_REJECTED','nodes':conflicts};break
 parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);records.append({**q,'mode':mode,'answer':answer})
result={'status':'COMPLETE_DIAGNOSTIC' if failure is None else 'INCOMPLETE_NOT_PUBLISHABLE','records':records,'attempts':attempts,'failure':failure,'completed_connections':len(records),'required_connections':len(queries),'fallbacks':fallbacks,'ledger':dict(ledger),'graph_sha256':digest,'scale':rc.scale,'budget_integer':budget,'total_context_query_seconds':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(records),'/',len(queries),'fallbacks',fallbacks,'failure',failure)
