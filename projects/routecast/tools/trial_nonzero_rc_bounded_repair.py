"""Frozen four-repair resource-based policy on full nonzero-RC cohort."""
import json,heapq
from pathlib import Path
from collections import Counter,defaultdict,deque
from fractions import Fraction
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
from native_capacity_rc_search import NativeCapacityRC
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_bounded_repair_2026-10-06';out.mkdir();parent=root/'experiments/nonzero_rc_fanout_observable64_2026-10-06';pr=json.loads((parent/'receipt.json').read_text());proof=json.loads((parent/'verification.json').read_text());assert sha(parent/'receipt.json')==proof['receipt_sha256'];assert all(sha(p)==h for p,h in pr['files_sha256'].items());graph,digest,nodes,f,rc,queries,_=load(root);budget=(Fraction(1,10**9)*rc.scale).__floor__();slots={f['edge_ids'][i]:(u,f['dest_ranks'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};out.joinpath('protocol.json').write_text(json.dumps({'max_repairs':4,'budget_integer':budget,'scale':rc.scale,'max_labels':10000,'order':'NET/pin; on failure retry failed pin first, then all released NET pins, then untouched pending order','blockers':'All owners on capacity-full nodes of unoccupied minimum-delay path, excluding current NET','graph_sha256':digest},indent=2)+'\n');native=NativeCapacityRC(rc);ledger=Counter();unions=defaultdict(set);records={};events=[];pending=deque(queries);repairs=0;terminal=None
key=lambda q:(q['net_id'],q['pin_index'])
def shortest(q):
 src,sink=q['source'],q['sink'];dist={src:rc.initial(src)};parents={};heap=[(dist[src],src)]
 while heap:
  delay,u=heapq.heappop(heap)
  if dist[u]!=delay:continue
  if u==sink:
   path=[];node=u
   while node!=src:prev,eid=parents[node];path.append(eid);node=prev
   return delay,path[::-1]
  for i in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][i]
   if not f['capacities'][v]:continue
   nd=delay+rc.increments[i]
   if v not in dist or nd<dist[v]:dist[v]=nd;parents[v]=(u,f['edge_ids'][i]);heapq.heappush(heap,(nd,v))
 return None,None
while pending:
 q=pending.popleft();assert key(q) not in records;other=Counter(ledger)
 for n in unions[q['net_id']]:other[n]-=1
 native.set_other(dict(+other));answer=native.query(q['source'],q['sink'],budget,max_labels=10000);event={'type':'QUERY',**q,'result':answer};events.append(event)
 if answer['status']=='FOUND':
  used={q['source']};node=q['source']
  for eid in answer['physical_edge_ids']:u,v=slots[eid];assert u==node;node=v;used.add(node)
  assert node==q['sink'];ledger.update(used-unions[q['net_id']]);unions[q['net_id']].update(used);records[key(q)]={**q,'result':answer};continue
 if answer['status']!='UNREACHABLE' or repairs>=4:terminal=answer['status'];break
 delay,path=shortest(q)
 if path is None or delay>budget:terminal='UNCONSTRAINED_BUDGET_FAILURE';break
 used={q['source']}|{slots[eid][1] for eid in path};blockers=set();blocked=[]
 for n in sorted(used):
  if other[n]>=f['capacities'][n]:
   owners={net for net,union in unions.items() if net!=q['net_id'] and n in union};blockers.update(owners);blocked.append({'node':n,'owners':sorted(owners)})
 if not blockers:terminal='NO_RESOURCE_BLOCKERS';break
 released_records=[list(k) for k in sorted(records) if k[0] in blockers];released_nodes={str(net):sorted(unions[net]) for net in sorted(blockers)}
 for net in blockers:
  for n in unions[net]:assert ledger[n]>=1;ledger[n]-=1
  del unions[net]
 records={k:r for k,r in records.items() if k[0] not in blockers};repairs+=1;events.append({'type':'RELEASE','repair':repairs,'failed_key':list(key(q)),'blockers':sorted(blockers),'blocked_nodes':blocked,'unoccupied_delay_integer':delay,'unoccupied_path':path,'released_records':released_records,'released_nodes':released_nodes});retry=[x for x in queries if x['net_id'] in blockers];pending=deque([q]+retry+[x for x in pending if x['net_id'] not in blockers]);print('repair',repairs,'failed',key(q),'blockers',sorted(blockers),flush=True)
arcs=defaultdict(set)
for row in records.values():
 for eid in row['result']['physical_edge_ids']:u,v=slots[eid];arcs[(row['net_id'],v)].add((u,eid))
bad=[{'net':net,'node':n,'parents':len(p)} for (net,n),p in arcs.items() if len(p)>1];overflow={n:v-f['capacities'][n] for n,v in ledger.items() if v>f['capacities'][n]};status='COMPLETE_DIAGNOSTIC' if not pending and terminal is None and len(records)==len(queries) and not bad and not overflow else 'INCOMPLETE_NOT_PUBLISHABLE';result={'status':status,'records':list(records.values()),'events':events,'terminal':terminal,'repairs':repairs,'required_connections':len(queries),'completed_connections':len(records),'multi_parent_nodes':bad,'overflow_nodes':overflow,'graph_sha256':digest,'scale':rc.scale,'budget_integer':budget,'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__)),'context_sha256':sha(root/'tools/nonzero_rc_search_context.py'),'scope':'Frozen max4 repair attempts, fixed1ns, exact buffered path constraints, all NET endpoints attempted; incomplete stage never publishable. No native local/residual OPIN, nonconfigurable closure, FULL/STA or speed/generalization claim.'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(status,len(records),terminal,len(bad),sum(overflow.values()))
