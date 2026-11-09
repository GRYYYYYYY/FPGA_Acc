"""Exact relaxed/residual shortest-delay diagnostics at terminal failed query."""
import json,heapq
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
from persistent_rc_context import PersistentRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/mux_capacity_avoid_reroute_2026-10-06';alloc=ROOT/'experiments/mux_capacity_budgets_2026-10-06';out=ROOT/'experiments/mux_residual_failure_2026-10-06';out.mkdir();p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());rows=[];last=None
(out/'protocol.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(parent/'receipt.json'),source_sha256=sha(Path(__file__)),policy='All12 outcomes; terminal failed QUERY state equals final partial ledger. Full integer Dijkstra with selected endpoint-pair exclusion, relaxed then residual occupancy; no label limit, history ignored for minimum-delay diagnostic.'),indent=2)+'\n')
for case,row in zip(p['cases'],r['rows']):
 w,i=case['width'],case['index']
 if row['status']=='ALLOCATION_NOT_SUBMITTED':rows.append(dict(width=w,index=i,status=row['status']));continue
 pf=parent/f'w{w}_m{i}/prediction.json';assert sha(pf)==row['prediction_sha256'];d=json.loads(pf.read_text());q=d['failure']['query'];assert d['events'][-1]['type']=='QUERY' and d['events'][-1]['query']==q and not d['events'][-1]['committed']
 if w!=last:ctx=PersistentRCContext(case['old']);last=w
 ctx.bind_endpoints(case['target']);f=ctx.rc.fields;inc=ctx.rc.increments;slots={f['edge_ids'][s]:(u,f['dest_ranks'][s]) for u in range(len(ctx.context[2])) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};unions=defaultdict(set)
 for rec in d['records']:
  union=unions[rec['net_id']];union.add(rec['source'])
  for eid in rec['answer']['physical_edge_ids']:u,v=slots[eid];union.update((u,v))
 ledger=Counter(n for union in unions.values() for n in union);assert dict(ledger)=={int(n):c for n,c in d['ledger'].items()};other={n:c-int(n in unions[q['net_id']]) for n,c in ledger.items()};af=alloc/f'w{w}_m{i}.json';a=json.loads(af.read_text());pairs={(x['source'],x['sink']) for x in ctx.context[5] if x['net_id']==a['selected_net']};restriction={a['forbidden_rank']} if (q['source'],q['sink']) in pairs else set();budget=min(int(F(a['budgets_ns'][str(q['connection_id'])])*ctx.rc.scale/10**9),ctx.rc.scale//10**9);certs={}
 for mode in ('relaxed','residual'):
  blocked=restriction|({n for n,c in other.items() if c>=f['capacities'][n]} if mode=='residual' else set());dist={};pred={};heap=[]
  if q['source'] not in blocked:dist[q['source']]=0;heap=[(0,q['source'])]
  while heap:
   value,u=heapq.heappop(heap)
   if value!=dist[u]:continue
   for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][s]
    if v in blocked or f['capacities'][v]<=0:continue
    value2=value+inc[s]
    if v not in dist or value2<dist[v]:dist[v]=value2;pred[v]=s;heapq.heappush(heap,(value2,v))
  path=[];n=q['sink']
  if n in dist:
   while n!=q['source']:s=pred[n];path.append(n);n=slots[f['edge_ids'][s]][0]
   path.append(n);path.reverse()
  certs[mode]=dict(blocked=sorted(blocked),minimum=dist.get(q['sink']),within_budget=q['sink'] in dist and dist[q['sink']]<=budget,distances={str(n):v for n,v in dist.items()},predecessor_slots={str(n):s for n,s in pred.items()},path_nodes=path)
 blocked_witness=[dict(node=n,owners=sorted(net for net,union in unions.items() if net!=q['net_id'] and n in union)) for n in certs['relaxed']['path_nodes'] if other.get(n,0)>=f['capacities'][n]]
 file=out/f'w{w}_m{i}.json';file.write_text(json.dumps(dict(target=case['target'],graph_sha256=ctx.context[1],prediction_sha256=sha(pf),allocation_sha256=sha(af),query=q,budget=budget,scale=ctx.rc.scale,restriction=sorted(restriction),other={str(n):c for n,c in other.items() if c},certificates=certs,relaxed_witness_blockers=blocked_witness),indent=2)+'\n');result=dict(width=w,index=i,relaxed_within_budget=certs['relaxed']['within_budget'],residual_within_budget=certs['residual']['within_budget'],witness_blockers=len(blocked_witness),sha256=sha(file));rows.append(result);print(result,flush=True)
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
