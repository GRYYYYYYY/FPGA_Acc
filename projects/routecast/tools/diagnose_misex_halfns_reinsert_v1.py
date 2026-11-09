"""Independent conditioned minima for frozen misex3 fifth batch failure."""
import json,sys,heapq,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
parent=R/'experiments/mcnc_bounded_owner_halfns_cache_v6_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3';out=R/'experiments/misex_halfns_reinsert_diagnosis_v1_2026-10-07';out.mkdir();eventfile=parent/'misex3/batch5.json';ep=base/'endpoints.json';inputs={str(p):sha(p) for p in (eventfile,ep,parent/'receipt.json')};inputs.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()});sources=closure([Path(__file__)]);protocol=dict(inputs=inputs,sources=sources,conditions=['unrestricted','working_owners','without_trigger_NET','before_batch_owners'],scope='Exact input-only min delay diagnostic, no candidate commit or native quality; all conditions retained.');(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
event=json.loads(eventfile.read_text());q=event['batch_failure']['query'];tick=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(ep);context=time.perf_counter()-tick;slots={e:s for s,e in enumerate(f['edge_ids'])}
def owners(records):
 own=defaultdict(set)
 for r in records:
  own[r['net_id']].add(r['source']);own[r['net_id']].update(f['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
 return own
working=owners(event['working_records']);before=owners(event['before_records']);assert not working[q['net_id']];ledger=Counter(n for ns in working.values() for n in ns);assert dict(ledger)=={int(k):v for k,v in event['working_ledger'].items()};reverse=[[] for _ in nodes]
for u in range(len(nodes)):
 for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][slot]].append((u,slot))
def minimum(blocked,backward=False):
 src,sink=q['source'],q['sink'];allowed=lambda n:f['capacities'][n]>blocked.get(n,0)
 if not allowed(src) or not allowed(sink):return None,None
 root=sink if backward else src;target=src if backward else sink;dist={root:0 if backward else rc.initial(src)};heap=[(dist[root],root)];back={}
 while heap:
  d,u=heapq.heappop(heap)
  if dist[u]!=d:continue
  if u==target:
   if backward:return d+rc.initial(src),None
   path=[];v=sink
   while v!=src:v,e=back[v];path.append(e)
   path.reverse();assert rc.path(src,sink,path)==d;return d,path
  arcs=reverse[u] if backward else ((f['dest_ranks'][s],s) for s in range(f['row_offsets'][u],f['row_offsets'][u+1]))
  for v,s in arcs:
   if not allowed(v):continue
   nd=d+rc.increments[s]
   if v not in dist or nd<dist[v]:dist[v]=nd;back[v]=(u,f['edge_ids'][s]);heapq.heappush(heap,(nd,v))
 return None,None
trigger=event['query']['net_id'];conditions=[('unrestricted',Counter()),('working_owners',ledger),('without_trigger_NET',Counter(n for net,ns in working.items() if net!=trigger for n in ns)),('before_batch_owners',Counter(n for net,ns in before.items() if net!=q['net_id'] for n in ns))];rows=[]
for mode,blocked in conditions:
 tick=time.perf_counter();d,path=minimum(blocked);rev,_=minimum(blocked,True);assert rev==d;rows.append(dict(condition=mode,minimum_integer=d,within_budget=d is not None and d<=event['batch_failure']['budget_integer'],physical_edge_ids=path,forward_reverse_equal=True,seconds=time.perf_counter()-tick));print(mode,d,flush=True)
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),context_seconds=context,query=q,budget_integer=event['batch_failure']['budget_integer'],scale=rc.scale,trigger_net_id=trigger,failed_net_has_no_retained_tree=True,rows=rows),indent=2)+'\n')
