"""Post-outcome single batch order ablation; no budget/owner-set changes."""
import json,sys,time,heapq
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from tree_floor_predictor_seed_v3 import predict
base=R/'experiments/mcnc_prospective_v1_2026-10-07/dsip';parent=R/'experiments/mcnc_bounded_owner_sequence_v1_2026-10-07/dsip';out=R/'experiments/dsip_reinsert_order_v1_2026-10-07';out.mkdir();eventfile=parent/'batch8.json';floorfile=parent/'floors.json';event=json.loads(eventfile.read_text());ep=json.loads((base/'endpoints.json').read_text());inputs={str(p):sha(p) for p in (eventfile,floorfile,base/'endpoints.json')};inputs.update({v['path']:v['sha256'] for v in ep['inputs'].values()});sources=closure([Path(__file__)])
protocol=dict(inputs=inputs,sources=sources,policies=['NET/CID ascending','ascending number of removed connections per NET, NET/CID ties'],selection='Exactly archived dsip batch8, retain failed query first, same wholeNET release set, budgets, kept trees and query cohort. Both policies retained regardless of outcome.',scope='Post-outcome development diagnostic. Not new untouched trial or full sequence. Costs exclude earlier context/floor/state generation except new model load separately paid; no native labels or QoR input.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter();graph,digest,nodes,f,rc,_=load_endpoints(base/'endpoints.json');construction=time.perf_counter()-start;floors={(q['source'],q['sink']):q['minimum_integer'] for q in json.loads(floorfile.read_text())};qid=event['batch_failure']['query'];eid_slot={eid:s for s,eid in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in event['working_records']:
 owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][eid_slot[e]] for e in rec['answer']['physical_edge_ids'])
assert not owners[qid['net_id']];ledger=Counter(n for ns in owners.values() for n in ns);assert dict(ledger)=={int(n):v for n,v in event['working_ledger'].items()}
def shortest(blocked):
 src,sink=qid['source'],qid['sink'];allowed=lambda n:f['capacities'][n]>blocked.get(n,0)
 if not allowed(src):return None,None
 dist={src:rc.initial(src)};back={};heap=[(dist[src],src)]
 while heap:
  d,u=heapq.heappop(heap)
  if d!=dist[u]:continue
  if u==sink:
   path=[];v=sink
   while v!=src:v,e=back[v];path.append(e)
   path.reverse();assert rc.path(src,sink,path)==d;return d,path
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][s]
   if not allowed(v):continue
   nd=d+rc.increments[s]
   if v not in dist or nd<dist[v]:dist[v]=nd;back[v]=(u,f['edge_ids'][s]);heapq.heappush(heap,(nd,v))
 return None,None
reverse=[[] for _ in nodes]
for u in range(len(nodes)):
 for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][s]].append((u,s))
def reverse_min(blocked):
 src,sink=qid['source'],qid['sink'];allowed=lambda n:f['capacities'][n]>blocked.get(n,0);dist={};heap=[]
 if allowed(sink):dist[sink]=0;heap=[(0,sink)]
 while heap:
  d,v=heapq.heappop(heap)
  if d!=dist[v]:continue
  if v==src:return d+rc.initial(src)
  for u,s in reverse[v]:
   if not allowed(u):continue
   nd=d+rc.increments[s]
   if u not in dist or nd<dist[u]:dist[u]=nd;heapq.heappush(heap,(nd,u))
 return None
conditions={};budget=event['batch_failure']['budget_integer']
for mode,blocked in [('unrestricted',{}),('working_owners',ledger),('without_reinserted_NET0',Counter(n for net,ns in owners.items() if net!=0 for n in ns))]:
 d,path=shortest(blocked);assert reverse_min(blocked)==d;conditions[mode]=dict(minimum_integer=d,edge_ids=path,within_budget=d is not None and d<=budget)
released=set(event['released_net_ids']);before=event['before_records'];kept=[q for q in before if q['net_id'] not in released];removed=[q for q in before if q['net_id'] in released];counts=Counter(q['net_id'] for q in removed);rows=[]
for index,policy in enumerate(protocol['policies']):
 ordered=sorted(removed,key=lambda q:((q['net_id'],q['connection_id']) if index==0 else (counts[q['net_id']],q['net_id'],q['connection_id'])));queries=[event['query']]+[{k:q[k] for k in ('connection_id','net_id','source','sink')} for q in ordered];tick=time.perf_counter();state=predict(f,rc,queries,floors,seed_records=kept);elapsed=time.perf_counter()-tick
 if index==0:assert state['records']==event['working_records'] and state['failure']==event['batch_failure'] and state['ledger']==event['working_ledger']
 file=out/f'policy{index}.json';file.write_text(json.dumps(state)+'\n');rows.append(dict(policy=policy,seconds=elapsed,committed=state['failure'] is None,completed=state['completed_connections'],failure=state['failure'],batch_connection_order=[q['connection_id'] for q in queries],candidate_sha256=sha(file)));print(index,state['failure'] is None,state['failure'],flush=True)
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),scale=rc.scale,budget_integer=budget,failed_query=qid,failed_net_has_no_retained_tree=True,conditions=conditions,context_seconds=construction,removed_counts=dict(counts),rows=rows),indent=2)+'\n')
