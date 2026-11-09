"""Frozen-otherNET exact buffered minimum delay for bound timing-feedback outputs."""
import heapq,json,time
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_top3_empty_delay_2026-10-06';out.mkdir();parent=root/'experiments/ex5p_critical_coupled2_2026-10-06/receipt.json';prior=json.loads(parent.read_text());proof=json.loads((parent.parent/'verification.json').read_text());assert proof['receipt_sha256']==sha(parent);targetfile=root/'experiments/ex5p_top3_complete_cohort_2026-10-06/receipt.json';targets=json.loads(targetfile.read_text())['bindings'];ep=root/'experiments/ex5p_placement_swap_2026-10-06/endpoints.json';(out/'protocol.json').write_text(json.dumps({'parent_sha256':sha(parent),'targets_sha256':sha(targetfile),'endpoint_sha256':sha(ep),'query_ids':[x['connection_id'] for x in targets],'policy':'Exact additive buffered-delay Dijkstra with zero otherNET demand; architecture capacities retained; each target independent. Full clipped lowerbound potentials saved. Diagnostic only; not joint commit or native timing guarantee.'},indent=2)+'\n');g,d,n,f,rc,queries=load_endpoints(ep);byid={q['connection_id']:q for q in queries};slots={f['edge_ids'][s]:(u,f['dest_ranks'][s]) for u in range(len(n)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};unions=defaultdict(set);parents=defaultdict(dict)
for rec in prior['records']:
 net=rec['net_id'];unions[net].add(rec['source'])
 for eid in rec['answer']['physical_edge_ids']:u,v=slots[eid];unions[net].add(v);parents[net][v]=(u,eid)
records=[];start=time.monotonic()
for t in targets:
 q=byid[t['connection_id']];other={int(k):v-int(int(k) in unions[q['net_id']]) for k,v in prior['ledger'].items()};other={};src,sink=q['source'],q['sink'];assert other.get(src,0)<f['capacities'][src];dist={src:rc.initial(src)};back={};heap=[(dist[src],src)]
 while heap:
  delay,u=heapq.heappop(heap)
  if delay!=dist[u]:continue
  if u==sink:break
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][s]
   if other.get(v,0)>=f['capacities'][v]:continue
   nd=delay+rc.increments[s]
   if v not in dist or nd<dist[v]:dist[v]=nd;back[v]=(u,f['edge_ids'][s]);heapq.heappush(heap,(nd,v))
 assert u==sink;path=[];node=sink;conflicts=[]
 while node!=src:
  previous,eid=back[node]
  if node in parents[q['net_id']] and parents[q['net_id']][node]!=(previous,eid):conflicts.append(node)
  node=previous;path.append(eid)
 old=next(r for r in prior['records'] if r['connection_id']==q['connection_id']);records.append({'query':q,'other_demand':other,'delay_integer':delay,'old_delay_integer':old['answer']['delay'],'physical_edge_ids':path[::-1],'potential_integer':[min(dist.get(k,delay),delay) for k in range(len(n))],'own_tree_parent_conflicts':conflicts})
r={'records':records,'scale':rc.scale,'graph_sha256':d,'query_s':time.monotonic()-start,'parent_sha256':sha(parent),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print([(x['query']['connection_id'],float((x['old_delay_integer']-x['delay_integer'])/rc.scale)*1e9,len(x['own_tree_parent_conflicts'])) for x in records])
