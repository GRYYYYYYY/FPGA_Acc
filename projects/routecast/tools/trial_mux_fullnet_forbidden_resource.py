"""Exact integer shortest delays with one observed contested RR rank forbidden."""
import json,heapq
from collections import Counter
from fractions import Fraction
from pathlib import Path
from persistent_rc_context import PersistentRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/mux_allfanin_priority32_2026-10-06';alloc=ROOT/'experiments/mux_allfanin_budgets_2026-10-06';out=ROOT/'experiments/mux_fullnet_forbidden_resource_2026-10-06';out.mkdir()
p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());rows=[];last=None
(out/'protocol.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(parent/'receipt.json'),source_sha256=sha(Path(__file__)),policy='All12 outcomes; each searched case picks most frequent release-frontier rank, lowest rank tie. Every target connection of every NET represented at releases involving that rank; one certificate per source. Full integer Dijkstra, zero other occupancy, one forbidden rank, no label limit. Retrospective diagnostic, not online routing policy.'),indent=2)+'\n')
for c,row in zip(p['cases'],r['rows']):
 w,i=c['width'],c['index'];assert (w,i)==(row['width'],row['index'])
 if row['status']=='ALLOCATION_NOT_SUBMITTED':rows.append(dict(width=w,index=i,status=row['status']));continue
 if w!=last:ctx=PersistentRCContext(c['old']);last=w
 ctx.bind_endpoints(c['target']);fields=ctx.rc.fields;inc=ctx.rc.increments
 prediction=parent/f'w{w}_m{i}/prediction.json';assert sha(prediction)==row['prediction_sha256'];d=json.loads(prediction.read_text());releases=[e for e in d['events'] if e['type']=='RELEASE'];freq=Counter(n for e in releases for n in e['frontier']);node=min(freq,key=lambda n:(-freq[n],n));queries={e['failed_query']['connection_id']:e['failed_query'] for e in releases if node in e['frontier']};nets={q['net_id'] for q in queries.values()};queries={q['connection_id']:q for q in ctx.context[5] if q['net_id'] in nets};af=alloc/f'w{w}_m{i}.json';a=json.loads(af.read_text());answers=[];certificates={}
 for cid,q in sorted(queries.items()):
  source,sink=q['source'],q['sink']
  if str(source) in certificates:
   cert=certificates[str(source)];dist={int(n):v for n,v in cert['distances'].items()};budget=min(int(Fraction(a['budgets_ns'][str(cid)])*ctx.rc.scale/10**9),ctx.rc.scale//10**9);answers.append(dict(query=q,budget=budget,minimum=dist.get(sink),within_budget=sink in dist and dist[sink]<=budget,certificate_source=str(source)));continue
  dist={};pred={};heap=[]
  if source!=node:dist[source]=0;heap=[(0,source)]
  while heap:
   value,u=heapq.heappop(heap)
   if dist[u]!=value:continue
   for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
    v=fields['dest_ranks'][slot]
    if v==node or fields['capacities'][v]<=0:continue
    cost=value+inc[slot]
    if v not in dist or cost<dist[v]:dist[v]=cost;pred[v]=slot;heapq.heappush(heap,(cost,v))
  budget=min(int(Fraction(a['budgets_ns'][str(cid)])*ctx.rc.scale/10**9),ctx.rc.scale//10**9)
  certificates[str(source)]=dict(distances={str(n):v for n,v in dist.items()},predecessor_slots={str(n):s for n,s in pred.items()});answers.append(dict(query=q,budget=budget,minimum=dist.get(sink),within_budget=sink in dist and dist[sink]<=budget,certificate_source=str(source)))
 file=out/f'w{w}_m{i}.json';file.write_text(json.dumps(dict(graph_sha256=ctx.context[1],target=c['target'],allocation_sha256=sha(af),prediction_sha256=sha(prediction),forbidden_rank=node,physical_node_id=int(ctx.context[2][node].get('id')),frequency=freq[node],scale=ctx.rc.scale,certificates=certificates,answers=answers),indent=2)+'\n');result=dict(width=w,index=i,forbidden_rank=node,queries=len(answers),within_budget=sum(x['within_budget'] for x in answers),sha256=sha(file));rows.append(result);print(result,flush=True)
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
