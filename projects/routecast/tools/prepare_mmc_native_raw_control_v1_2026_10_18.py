"""Dirty-only raw floor control; no full old-state floor construction."""
import json,time,heapq,resource
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_native_raw_control_v1_2026-10-18';D.mkdir(exist_ok=False);(D/'certificates').mkdir();start=time.perf_counter();G=R/'experiments/mmc_native_state_geometry_v1_2026-10-18';P=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18';pp=P/'staged_input_verification_v1.json';proof=json.loads(pp.read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());g=json.loads((G/'protocol.json').read_text());oldfile=Path(g['previous_endpoint']);newfile=P/'demand/endpoints.json';old=json.loads(oldfile.read_text());new=json.loads(newfile.read_text());dirty=set(proof['affected']['affected_net_ids']);bindings={**proof['bindings'],str(pp):sha(pp),str(G/'protocol.json'):sha(G/'protocol.json'),str(oldfile):sha(oldfile),str(newfile):sha(newfile),str(Path(__file__)):sha(__file__)};route=Path(g['previous_native_route']);bindings[str(route)]=sha(route)
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,dirty_nets=sorted(dirty),dirty_connections=480,policy='All new endpoint closure queries; source-group exact additive raw Dijkstra over positive-capacity nodes, no owner or price constraints. Preserve all unchanged old native physical paths. No old floor search. Inherited floor_integer explicitly null, native delay is not mislabeled as a floor. Budgets irrelevant to seed-only raw control: inherited budget=max(1ns,actual native additive delay), dirty budget=max(1ns,ceil1.5Fnew). This is not the local anchored proxyV1 budget policy.',scope='Raw seed-control preparation, not feedback or target native routing. All old import and conversions paid to this control when used in continuous harness.'),f,indent=2);f.write('\n')
print('MMC RAW GRAPH/OLD ROUTE IMPORT START',flush=True)
graph,digest,nodes,fields,rc,queries=load_endpoints(newfile);state,nativerows,ledger=load_complete(route,old,nodes,fields,rc);import_seconds=time.perf_counter()-start;oldq={q['connection_id']:q for q in old['connections']};nativerows={r['connection_id']:r for r in nativerows};groups=defaultdict(list)
for q in queries:
 if q['net_id'] in dirty:groups[q['source']].append(q)
assert sum(len(qs) for qs in groups.values())==480
certs=[];fresh={};search_tick=time.perf_counter()
for ordinal,(source,qs) in enumerate(sorted(groups.items())):
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
 witnesses={}
 for q in qs:
  target=q['sink'];node=target;edges=[];seen=set()
  while node!=source:
   assert node not in seen;seen.add(node);node,slot=pred[node];edges.append(fields['edge_ids'][slot])
  edges.reverse();floor=dist[target];assert rc.path(source,target,edges)==floor;budget=max(rc.scale//10**9,(3*floor+1)//2);fresh[q['connection_id']]=dict(q,answer=dict(status='FOUND',physical_edge_ids=edges,delay=floor),floor_integer=floor,budget_integer=budget);witnesses[str(target)]=edges
 clip=max(dist[t] for t in targets);c=D/f'certificates/source_{source}.json'
 with c.open('x') as f:json.dump(dict(source=source,clip=clip,potentials={n:v for n,v in dist.items() if v<clip},witnesses=witnesses),f,separators=(',',':'));f.write('\n')
 certs.append(dict(path=str(c),sha256=sha(c)));print('MMC RAW SOURCE',ordinal+1,'/',len(groups),'settled',len(settled),flush=True)
search_seconds=time.perf_counter()-search_tick;records=[];owners=defaultdict(set);parents=defaultdict(dict);slots={eid:i for i,eid in enumerate(fields['edge_ids'])}
for q in queries:
 cid=q['connection_id'];net=q['net_id']
 if cid in fresh:rec=fresh[cid]
 else:
  assert q==oldq[cid];r=nativerows[cid];rec=dict(q,answer=dict(status='FOUND',physical_edge_ids=r['physical_edge_ids'],delay=r['delay_integer']),floor_integer=None,budget_integer=max(rc.scale//10**9,r['delay_integer']))
 records.append(rec);u=q['source'];seen={u};owners[net].add(u)
 for eid in rec['answer']['physical_edge_ids']:
  slot=slots[eid];assert fields['row_offsets'][u]<=slot<fields['row_offsets'][u+1];v=fields['dest_ranks'][slot];assert v not in seen;seen.add(v);edge=(u,fields['switch_ids'][slot])
  if nodes[v].get('type')!='SINK':assert v not in parents[net] or parents[net][v]==edge;parents[net][v]=edge
  owners[net].add(v);u=v
 assert u==q['sink'] and rec['answer']['delay']<=rec['budget_integer']
occupancy=Counter(n for used in owners.values() for n in used);overflow=sum(max(0,v-fields['capacities'][n]) for n,v in occupancy.items());frame=dict(records=sorted(records,key=lambda r:r['connection_id']),scale=rc.scale,required_connections=len(queries),completed_connections=len(records),ledger=dict(occupancy),overflow_units=overflow,eligible_for_legal_route_commit=False,budget_policy='RAW_CONTROL_NO_OLD_FLOORS',scope='Seed-only complete demand prediction; inherited old floors unknown, no feedback or native acceptance.')
with (D/'initial.json').open('x') as f:json.dump(frame,f);f.write('\n')
for spec in new['inputs'].values():bindings[spec['path']]=spec['sha256']
for name in ['compact_stream_rc_endpoint_context_v1.py','load_complete_route_state_v1.py','native_route_ledger_import_compact.py']:bindings[str(R/'tools'/name)]=sha(R/'tools'/name)
bindings[str(D/'initial.json')]=sha(D/'initial.json');assert all(sha(p)==h for p,h in bindings.items())
with (D/'receipt.json').open('x') as f:json.dump(dict(bindings=bindings,certificates=certs,dirty_nets=sorted(dirty),recomputed_connections=len(fresh),preserved_connections=len(records)-len(fresh),source_searches=len(groups),import_seconds=import_seconds,dirty_search_and_certificates_seconds=search_seconds,total_seconds_before_receipt=time.perf_counter()-start,overflow_units=overflow,maxrss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,independent_verification_pending=True,scope='No full old floor production and no target native routing; independent floor/path/RC/parent/ledger proof pending.'),f,indent=2);f.write('\n')
print('MMC RAW COMPLETE',len(records),'connections','overflow',overflow,flush=True)
