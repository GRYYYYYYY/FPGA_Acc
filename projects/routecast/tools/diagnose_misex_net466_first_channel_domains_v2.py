"""Budget-feasible first-CHAN supersets and finite Hall capacity cuts."""
import sys,json,time,heapq,struct,itertools
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
parent=R/'experiments/misex_net466_extra_owner_joint_v13_2026-10-07';out=R/'experiments/misex_net466_first_channel_domains_v2_2026-10-07';out.mkdir();eventpath=parent/'event.json';ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';floorspath=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';proofpath=parent/'branch_verification_dedup.json';proof=json.loads(proofpath.read_text());assert proof['bindings'][str(eventpath)]==sha(eventpath);bindings={**closure([Path(__file__)]),str(eventpath):sha(eventpath),str(ep):sha(ep),str(floorspath):sha(floorspath),str(proofpath):sha(proofpath)};bindings.update({row['path']:row['sha256'] for row in json.loads(ep.read_text())['inputs'].values()});criticalpath=R/'experiments/misex_net466_failure_minima_v8_2026-10-07/receipt.json';bindings[str(criticalpath)]=sha(criticalpath);release=[24,113,157,165,180,258,331,334,384];(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,release=release,query_policy='Earliest CID per released NET, all five new pending queries, and all distinct frozen first16 v14 failed queries in this release scope',scope='Necessary ordinary additive-RC first-channel Hall capacity condition for fixed kept, ignores joint tree restrictions; no native or global feasibility inference.'),indent=2)+'\n');begin=time.perf_counter();_,_,nodes,f,rc,_=load_endpoints(ep);event=json.loads(eventpath.read_text());slot={edge:i for i,edge in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in event['before_records']:
 if rec['net_id'] not in release:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slot[edge]] for edge in rec['answer']['physical_edge_ids'])
occupancy=Counter(n for own in owners.values() for n in own);allowed=bytes(f['capacities'][n]>occupancy[n] for n in range(len(nodes)));(out/'allowed.bin').write_bytes(allowed);channel=[n.get('type') in ('CHANX','CHANY') for n in nodes];groups=defaultdict(list)
for rec in event['before_records']:
 if rec['net_id'] in release:groups[rec['net_id']].append({k:rec[k] for k in ['connection_id','net_id','source','sink']})
for q in event['selection']['queries']:groups[q['net_id']].append(q)
floors={(r['source'],r['sink']):r['minimum_integer'] for r in json.loads(floorspath.read_text())};reverse=[[] for _ in nodes]
for u in range(len(nodes)):
 for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][edge]].append((u,edge))
INF=(1<<64)-1;rows=[];selected={min(qs,key=lambda q:q['connection_id'])['connection_id']:min(qs,key=lambda q:q['connection_id']) for qs in groups.values()};selected.update({q['connection_id']:q for q in event['selection']['queries']})
for row in json.loads(criticalpath.read_text())['rows']:
 q=row['query']
 if q['net_id'] in groups:selected[q['connection_id']]=q
for q in sorted(selected.values(),key=lambda q:q['connection_id']):
 net=q['net_id'];source,sink=q['source'],q['sink'];budget=max(rc.scale//10**9,(3*floors[source,sink]+1)//2);dist={sink:0} if allowed[sink] else {};queue=[(0,sink)] if allowed[sink] else []
 while queue:
  delay,v=heapq.heappop(queue)
  if dist[v]!=delay:continue
  for u,edge in reverse[v]:
   candidate=delay+rc.increments[edge]
   if allowed[u] and candidate<dist.get(u,INF):dist[u]=candidate;heapq.heappush(queue,(candidate,u))
 prefix={source:rc.initial(source)} if allowed[source] else {};queue=[(rc.initial(source),source)] if allowed[source] else [];first={}
 while queue:
  delay,u=heapq.heappop(queue)
  if prefix[u]!=delay:continue
  for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][edge];candidate=delay+rc.increments[edge]
   if not allowed[v] or candidate>budget:continue
   if channel[v]:first[v]=min(candidate,first.get(v,INF))
   elif candidate<prefix.get(v,INF):prefix[v]=candidate;heapq.heappush(queue,(candidate,v))
 domain=sorted(v for v,d in first.items() if v in dist and d+dist[v]<=budget);path=out/f"cid{q['connection_id']}_reverse.bin";path.write_bytes(b''.join(struct.pack('<Q',dist.get(n,INF)) for n in range(len(nodes))));rows.append(dict(net=net,query=q,budget=budget,no_channel_path=sink in prefix,first_channel_domain=domain,reverse_file=str(path),reverse_sha256=sha(path)));print(net,q['connection_id'],len(domain),sink in prefix,flush=True)
active=defaultdict(list)
for row in rows:
 if not row['no_channel_path']:active[row['net']].append(row)
cuts=[]
for choice in itertools.product(*([None,*active[net]] for net in sorted(active))):
 subset=[row for row in choice if row is not None]
 if not subset:continue
 union=set(v for row in subset for v in row['first_channel_domain']);capacity=sum(f['capacities'][v]-occupancy[v] for v in union)
 if capacity<len(subset):cuts.append(dict(nets=[row['net'] for row in subset],query_ids=[row['query']['connection_id'] for row in subset],nodes=sorted(union),residual_capacity=capacity,required_distinct_nets=len(subset)))
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,release=release,rows=rows,hall_cuts=cuts,total_component_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');print('Hall cuts',len(cuts),flush=True)
