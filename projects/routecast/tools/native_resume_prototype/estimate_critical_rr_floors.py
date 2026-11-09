"""Target-only independent-connection buffered RC floors with clipped potential certificates."""
import heapq,json,sys,time
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
ROOT=Path(__file__).resolve().parents[2];width,index=map(int,sys.argv[1:]);assert (width,index) in ((16,1),(32,3))
out=ROOT/f'experiments/native_resume_critical_rr_floors_w{width}_m{index}_2026-10-07';out.mkdir(exist_ok=False);(out/'certificates').mkdir();start=time.perf_counter()
ep=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{width}_m{index}/target_endpoints.json';meta=json.loads(ep.read_text());inputs={str(ep):sha(ep),**{v['path']:v['sha256'] for v in meta['inputs'].values()}}
# Replay own native criticality snapshot, never cold-route quality.
log=ROOT/f'experiments/native_resume_decision_audit_2026-10-07/w{width}_m{index}_workflow/run.log'
inputs[str(log)]=sha(log)
events=[line.split() for line in log.read_text().splitlines() if line.startswith('RC_DECISION ')]
last=max(int(x[1]) for x in events)
pairs={(x[3],int(x[5])) for x in events if int(x[1])==last and float(x[9])>=float(x[10])}
selected=[q['connection_id'] for q in meta['connections'] if (meta['net_names'][str(q['net_id'])],q['sink']) in pairs]
assert len(selected)==len(pairs)
selection=dict(snapshot_call=last,log_sha256=sha(log),selected_connection_ids=sorted(selected),policy='Own candidate last working native inspection; criticality >= native threshold; no delay rejection filtering. Archived replay, not prospective initial selection; prior candidate generation cost excluded.')
protocol=dict(inputs=inputs,selection=selection,producer_sha256=sha(Path(__file__)),policy='Fixed own-current-criticality subset, sorted source grouping; positive-capacity RR nodes only, ignore all owner occupancy and shared-tree constraints. Exact additive buffered-RC minimum per connection. Selection uses own archived native criticality snapshot; floor search reads endpoints and graph only. Include source initial RC. No numeric delay budget or target cold labels.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
graph,digest,nodes,f,rc,queries=load_endpoints(ep);assert all(v>=0 for v in rc.increments);queries=[q for q in queries if q['connection_id'] in set(selected)];prepared=time.perf_counter();groups=defaultdict(list)
for q in queries:groups[q['source']].append(q)
rows=[];certs=[];slotsource=[u for u in range(len(nodes)) for slot in range(f['row_offsets'][u],f['row_offsets'][u+1])]
for ordinal,source in enumerate(sorted(groups)):
 targets={q['sink'] for q in groups[source]};remaining=set(targets);dist={source:rc.initial(source)};pred={};queue=[(dist[source],source)];settled=set();examined=0
 assert f['capacities'][source]>0
 while queue and remaining:
  value,u=heapq.heappop(queue)
  if u in settled or value!=dist[u]:continue
  settled.add(u);remaining.discard(u)
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   examined+=1;v=f['dest_ranks'][slot]
   if f['capacities'][v]<=0:continue
   candidate=value+rc.increments[slot]
   if candidate<dist.get(v,candidate+1):dist[v]=candidate;pred[v]=slot;heapq.heappush(queue,(candidate,v))
 cap=max(dist[t] for t in targets if t in settled) if not remaining else None
 cert=dict(source=source,clip=cap,potentials={str(n):v for n,v in dist.items() if cap is not None and v<cap},settled_nodes=len(settled),examined_edges=examined)
 file=out/f'certificates/source_{source}.json';file.write_text(json.dumps(cert,separators=(',',':'))+'\n');certs.append(dict(source=source,path=str(file),sha256=sha(file)))
 for q in groups[source]:
  target=q['sink'];path=[]
  if target in settled:
   n=target
   while n!=source:slot=pred[n];path.append(f['edge_ids'][slot]);n=slotsource[slot]
   path.reverse();assert rc.path(source,target,path)==dist[target]
  rows.append(dict(query=q,status='FOUND' if target in settled else 'UNREACHABLE',minimum_integer=dist[target] if target in settled else None,physical_edge_ids=path if target in settled else None))
 if ordinal%100==0:print(width,'sources',ordinal+1,'/',len(groups),flush=True)
assert all(sha(file)==h for file,h in inputs.items())
receipt=dict(protocol_sha256=sha(out/'protocol.json'),graph_sha256=digest,scale=rc.scale,rows=rows,certificates=certs,preparation_seconds=prepared-start,query_and_certificate_seconds=time.perf_counter()-prepared,total_seconds=time.perf_counter()-start,scope='Independent relaxed path floors only; buffered additive model, no shared-tree loading, occupancy, legality or joint-route STA guarantee. Selected subset only, unqueried connections deliberately excluded, not failed. Candidate snapshot generation cost excluded; target context preparation included; no endpoint/frontend/RR generation or cold execution cost.')
(out/'receipt.json').write_text(json.dumps(receipt,separators=(',',':'))+'\n');print(width,'found',sum(x['status']=='FOUND' for x in rows),'/',len(rows),'seconds',receipt['total_seconds'],flush=True)
