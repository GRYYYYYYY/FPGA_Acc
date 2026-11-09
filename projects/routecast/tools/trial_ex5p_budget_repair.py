"""Four repairs maximum; exact residual cuts and wholeNET release, resource history."""
import json,time,heapq
from pathlib import Path
from collections import Counter,defaultdict,deque
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_capacity_rc_search import NativeCapacityRC
root=Path(__file__).resolve().parents[1];parent=root/'experiments/ex5p_bounded_history_repair_2026-10-06';prior=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json') ;ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json';out=root/'experiments/ex5p_budget_repair_2026-10-06';out.mkdir();(out/'protocol.json').write_text(json.dumps({'parent_sha256':sha(parent/'receipt.json'),'repairs_max':4,'budget_ns':1,'max_labels':10000,'policy':'Continue retained1898 paths, inherit recorded history; failed query first then incomplete original queries. OnUNREACHABLE choose exact no-demand minimum-delay path <=1ns; release all NET owners of full nodes on it, plus currentNET if partial; failedNET queries first, otherreleasedNETs next, add1 history for frontier nodes; retry failed then released allqueries then untouchedpending. Cost exactdelay*(1+historydest)*(1+otherdest); stop unsupported failure/tree conflict/empty-graph budget failure/4repair ceiling; no native path/timing.'},indent=2)+'\n');start=time.monotonic();graph,digest,nodes,f,rc,queries=load_endpoints(ep);native=NativeCapacityRC(rc);slots={f['edge_ids'][s]:(u,f['dest_ranks'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};dest_slots=defaultdict(list)
for s,n in enumerate(f['dest_ranks']):dest_slots[n].append(s);native.arrays[3][s]=rc.increments[s]
unions=defaultdict(set);parents=defaultdict(dict);records={q['connection_id']:q for q in prior['records']}
for q in prior['records']:
 net=q['net_id'];unions[net].add(q['source'])
 for eid in q['answer']['physical_edge_ids']:u,n=slots[eid];unions[net].add(n);parents[net][n]=(u,eid)
ledger=Counter(n for ns in unions.values() for n in ns);history=Counter({int(n):c for n,c in prior['history'].items()});
for n,c in history.items():
 for slot in dest_slots[n]:native.arrays[3][slot]=rc.increments[slot]*(1+c)
failed=prior['failure']['query'];pending=deque([failed]+[q for q in queries if q['connection_id'] not in records and q['connection_id']!=failed['connection_id']]);events=[];repairs=0;failure=None
while pending:
 q=pending.popleft();net=q['net_id'];other={n:c-int(n in unions[net]) for n,c in ledger.items()};other={n:c for n,c in other.items() if c};native.set_other(other);answer=native.query(q['source'],q['sink'],rc.scale//10**9,max_labels=10000);event={'type':'QUERY','query':q,'answer':answer,'committed':False};events.append(event)
 if answer['status']=='UNREACHABLE' and repairs<4:
  dist={q['source']:rc.initial(q['source'])};back={};heap=[(dist[q['source']],q['source'])]
  while heap:
   delay,u=heapq.heappop(heap)
   if delay!=dist[u]:continue
   if u==q['sink']:break
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    n=f['dest_ranks'][slot]
    if f['capacities'][n]==0:continue
    nd=delay+rc.increments[slot]
    if n not in dist or nd<dist[n]:dist[n]=nd;back[n]=(u,f['edge_ids'][slot]);heapq.heappush(heap,(nd,n))
  assert u==q['sink'];path=[];pathnodes={u};node=u
  while node!=q['source']:node,eid=back[node];path.append(eid);pathnodes.add(node)
  path=path[::-1]
  if delay>rc.scale//10**9:failure={'query':q,'status':'EMPTY_DEMAND_OVER_BUDGET'};break
  frontier=sorted(n for n in pathnodes if other.get(n,0)>=f['capacities'][n]);owners={n:sorted(k for k,ns in unions.items() if k!=net and n in ns) for n in frontier};blockers=sorted({k for ks in owners.values() for k in ks}|({net} if unions[net] else set()))
  if not blockers:failure={'query':q,'status':'NO_RELEASABLE_OWNER'};break
  removed=sorted(cid for cid,r in records.items() if r['net_id'] in blockers);released={k:sorted(unions[k]) for k in blockers}
  for k in blockers:ledger.subtract(unions[k]);del unions[k];del parents[k]
  ledger=+ledger
  for cid in removed:del records[cid]
  history.update(frontier)
  for n in frontier:
   for s in dest_slots[n]:native.arrays[3][s]=rc.increments[s]*(1+history[n])
  events.append({'type':'RELEASE','failed_query':q,'frontier':frontier,'empty_path':path,'empty_delay_integer':delay,'owners':owners,'blocker_NETs':blockers,'removed_connection_ids':removed,'released_unions':released,'history_after':dict(history)});repairs+=1;pending=deque([q]+[x for x in queries if x['net_id']==net and x['connection_id']!=q['connection_id'] and net in blockers]+[x for x in sorted(queries,key=lambda x:(x['net_id'],x['connection_id'])) if x['net_id'] in blockers and x['net_id']!=net]+[x for x in pending if x['net_id'] not in blockers]);continue
 if answer['status']!='FOUND':failure={'query':q,'status':answer['status']};break
 node=q['source'];used={node};incoming={}
 for eid in answer['physical_edge_ids']:u,n=slots[eid];assert u==node;node=n;used.add(n);incoming[n]=(u,eid)
 assert node==q['sink'];conflicts=[n for n,p in incoming.items() if n in parents[net] and parents[net][n]!=p]
 if conflicts:failure={'query':q,'status':'MULTI_PARENT_REJECTED','nodes':conflicts};break
 assert q['connection_id'] not in records;parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);records[q['connection_id']]={**q,'mode':'NATIVE_HISTORY_DELAY_COST','answer':answer};event['committed']=True
result={'status':'COMPLETE_DIAGNOSTIC' if failure is None else 'INCOMPLETE_NOT_PUBLISHABLE','records':[records[k] for k in sorted(records)],'completed_connections':len(records),'required_connections':len(queries),'events':events,'failure':failure,'repairs':repairs,'history':dict(history),'ledger':dict(ledger),'scale':rc.scale,'graph_sha256':digest,'total_context_repair_seconds':time.monotonic()-start,'parent_sha256':sha(parent/'receipt.json'),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(records),'/',len(queries),'repairs',repairs,'failure',failure)
