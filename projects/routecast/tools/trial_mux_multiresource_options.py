"""Two retrospective detour choices retaining the preceding resource exclusion."""
import json,heapq
from pathlib import Path
from persistent_rc_context import PersistentRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/mux_capacity_avoid_reroute_2026-10-06';residual=ROOT/'experiments/mux_residual_failure_2026-10-06';alloc=ROOT/'experiments/mux_capacity_budgets_2026-10-06';out=ROOT/'experiments/mux_multiresource_options_2026-10-06';out.mkdir();p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());rows=[];last=None
(out/'protocol.json').write_text(json.dumps(dict(cases=p['cases'],parent_receipt_sha256=sha(parent/'receipt.json'),residual_verification_sha256=sha(residual/'verification.json'),source_sha256=sha(Path(__file__)),policy='All12 outcomes. For each terminal relaxed-witness blocker, choices are failed NET or observed owner NET avoiding new resource. Preserve old selected NET resource prohibition; full target NET connections, relaxed other demand, exact integer Dijkstra, source certificates shared within option only. Retrospective diagnosis, not online routing.'),indent=2)+'\n')
for case,row in zip(p['cases'],r['rows']):
 w,i=case['width'],case['index']
 if row['status']=='ALLOCATION_NOT_SUBMITTED':rows.append(dict(width=w,index=i,status=row['status']));continue
 rf=residual/f'w{w}_m{i}.json';d=json.loads(rf.read_text());assert len(d['relaxed_witness_blockers'])==1;block=d['relaxed_witness_blockers'][0];af=alloc/f'w{w}_m{i}.json';a=json.loads(af.read_text());nets=sorted({d['query']['net_id'],*block['owners']})
 if w!=last:ctx=PersistentRCContext(case['old']);last=w
 ctx.bind_endpoints(case['target']);f=ctx.rc.fields;inc=ctx.rc.increments;options=[]
 for chosen in nets:
  restrictions={a['selected_net']:{a['forbidden_rank']}};restrictions.setdefault(chosen,set()).add(block['node']);certs={};answers=[]
  for query in ctx.context[5]:
   net=query['net_id']
   if net not in restrictions:continue
   forbidden=restrictions[net];source,sink=query['source'],query['sink'];key=str(source)+':'+','.join(map(str,sorted(forbidden)))
   if key not in certs:
    dist={};pred={};heap=[]
    if source not in forbidden:dist[source]=0;heap=[(0,source)]
    while heap:
     value,u=heapq.heappop(heap)
     if dist[u]!=value:continue
     for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
      v=f['dest_ranks'][slot]
      if v in forbidden or f['capacities'][v]<=0:continue
      candidate=value+inc[slot]
      if v not in dist or candidate<dist[v]:dist[v]=candidate;pred[v]=slot;heapq.heappush(heap,(candidate,v))
    certs[key]=dict(source=source,forbidden=sorted(forbidden),distances={str(n):v for n,v in dist.items()},predecessor_slots={str(n):s for n,s in pred.items()})
   cert=certs[key];answers.append(dict(query=query,certificate=key,minimum=cert['distances'].get(str(sink))))
  options.append(dict(chosen_net=chosen,restrictions={str(net):sorted(nodes) for net,nodes in restrictions.items()},certificates=certs,answers=answers))
 file=out/f'w{w}_m{i}.json';file.write_text(json.dumps(dict(target=case['target'],graph_sha256=ctx.context[1],scale=ctx.rc.scale,residual_sha256=sha(rf),allocation_sha256=sha(af),new_resource=block['node'],options=options),indent=2)+'\n');result=dict(width=w,index=i,choices=nets,queries=sum(len(x['answers']) for x in options),unreachable=sum(x['minimum'] is None for o in options for x in o['answers']),sha256=sha(file));rows.append(result);print(result,flush=True)
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
