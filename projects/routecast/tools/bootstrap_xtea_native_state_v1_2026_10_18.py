"""Frozen native-anchored estimator bootstrap, no placement update/native run."""
import json,time,heapq,hashlib
from pathlib import Path
from collections import defaultdict,Counter
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_native_state_bootstrap_v1_2026-10-18';D.mkdir(exist_ok=False);(D/'certificates').mkdir();start=time.perf_counter()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
pp=R/'experiments/native_state_bootstrap_protocol_v1_2026-10-18/protocol.json';protocol=json.loads(pp.read_text());bindings={**protocol['bindings'],str(pp):sha(pp),str(Path(__file__)):sha(__file__)};assert all(sha(p)==h for p,h in bindings.items())
ep=Path(protocol['previous_endpoint']);meta=json.loads(ep.read_text());route=Path(protocol['previous_native_route']);graph,digest,nodes,fields,rc,queries=load_endpoints(ep);state,native_rows,ledger=load_complete(route,meta,nodes,fields,rc);import_seconds=time.perf_counter()-start;delay={r['connection_id']:r['delay_integer'] for r in native_rows};groups=defaultdict(list)
for q in queries:groups[q['source']].append(q)
floors={};certificates=[];tick=time.perf_counter()
for source,qs in sorted(groups.items()):
 targets={q['sink'] for q in qs};remaining=set(targets);dist={source:rc.initial(source)};pred={};queue=[(dist[source],source)];settled=set()
 while queue and remaining:
  value,u=heapq.heappop(queue)
  if u in settled or value!=dist[u]:continue
  settled.add(u);remaining.discard(u)
  for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
   v=fields['dest_ranks'][slot]
   if fields['capacities'][v]<=0:continue
   candidate=value+rc.increments[slot]
   if candidate<dist.get(v,candidate+1):dist[v]=candidate;pred[v]=(u,slot);heapq.heappush(queue,(candidate,v))
 assert not remaining
 clip=max(dist[t] for t in targets);witnesses={}
 for target in targets:
  node=target;edges=[];seen=set()
  while node!=source:
   assert node not in seen;seen.add(node);node,slot=pred[node];edges.append(fields['edge_ids'][slot])
  edges.reverse();assert rc.path(source,target,edges)==dist[target];witnesses[str(target)]=edges
 for q in qs:floors[q['connection_id']]=dist[q['sink']]
 path=D/f'certificates/source_{source}.json'
 with path.open('x') as f:json.dump(dict(source=source,clip=clip,potentials={n:v for n,v in dist.items() if v<clip},witnesses=witnesses),f,separators=(',',':'));f.write('\n')
 certificates.append(dict(path=str(path),sha256=sha(path)))
records=[];anchored=0
for q in sorted(queries,key=lambda q:q['connection_id']):
 cid=q['connection_id'];floor=floors[cid];proxy=max(rc.scale//10**9,(3*floor+1)//2);budget=max(proxy,delay[cid]);assert floor<=delay[cid]<=budget;anchored+=delay[cid]>proxy
 records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=next(r['physical_edge_ids'] for r in native_rows if r['connection_id']==cid),delay=delay[cid]),floor_integer=floor,proxy_budget_integer=proxy,budget_integer=budget))
owners=defaultdict(set)
for q in queries:owners[q['net_id']].update(n for n,s in state[q['connection_id']])
occupancy=Counter(n for used in owners.values() for n in used);assert not any(v>fields['capacities'][n] for n,v in occupancy.items())
frame=dict(records=records,scale=rc.scale,required_connections=len(queries),completed_connections=len(records),ledger=dict(occupancy),history={},epochs={n:0 for n in owners},overflow_units=0,budget_policy='NATIVE_ANCHORED_PROXY_V1',scope='Native old-state initialization only; no update or acceptance publication.')
with (D/'initial.json').open('x') as f:json.dump(frame,f);f.write('\n')
with (D/'native_paths.json').open('x') as f:json.dump({cid:path for cid,path in state.items()},f);f.write('\n')
assert all(sha(p)==h for p,h in bindings.items())
for p in [D/'initial.json',D/'native_paths.json']:bindings[str(p)]=sha(p)
with (D/'receipt.json').open('x') as f:json.dump(dict(bindings=bindings,certificates=certificates,connections=len(records),nets=len(owners),source_groups=len(groups),anchored_above_original_proxy=anchored,import_seconds=import_seconds,floor_records_serialization_seconds=time.perf_counter()-tick,bootstrap_seconds_before_receipt=time.perf_counter()-start,scope='Graph/auth/import/all floor queries/certificates/serialization included before receipt. Prior native routing and independent proof excluded and explicit; no full workflow or speed claim.'),f,indent=2);f.write('\n')
print('BOOTSTRAP',len(records),'connections',len(owners),'NETs','anchored',anchored,'seconds',time.perf_counter()-start,flush=True)
