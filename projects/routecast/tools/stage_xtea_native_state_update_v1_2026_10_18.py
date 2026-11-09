"""Dirty wholeNET/sharedSOURCE staging from certified previous native state."""
import json,heapq,time,hashlib
from pathlib import Path
from collections import defaultdict,Counter
from affected_connections import affected
from class_cached_rc_endpoint_context_v1 import load_endpoints
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_native_state_staged_update_v1_2026-10-18';D.mkdir(exist_ok=False);(D/'certificates').mkdir();start=time.perf_counter()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=R/'experiments/xtea_native_state_bootstrap_v1_2026-10-18';proof=json.loads((base/'independent_xml_verification_v1.json').read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());targetroot=R/'experiments/xtea_native_state_new_swap_v1_2026-10-18';targetproof=json.loads((targetroot/'staged_input_verification_v1.json').read_text());assert all(sha(p)==h for p,h in targetproof['bindings'].items());oldpath=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json';ep=targetroot/'demand/endpoints.json';old=json.loads(oldpath.read_text());new=json.loads(ep.read_text());delta=affected(old,new);dirty=set(delta['affected_net_ids']);prior=json.loads((base/'initial.json').read_text());oldrecords={r['connection_id']:r for r in prior['records']};graph,digest,nodes,fields,rc,queries=load_endpoints(ep);assert rc.scale==prior['scale'];groups=defaultdict(list)
for q in queries:
 if q['net_id'] in dirty:groups[q['source']].append(q)
certificates=[];fresh={}
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
 witnesses={}
 for q in qs:
  node=q['sink'];edges=[];seen=set()
  while node!=source:
   assert node not in seen;seen.add(node);node,slot=pred[node];edges.append(fields['edge_ids'][slot])
  edges.reverse();floor=dist[q['sink']];assert rc.path(source,q['sink'],edges)==floor;budget=max(rc.scale//10**9,(3*floor+1)//2);fresh[q['connection_id']]=dict(q,answer=dict(status='FOUND',physical_edge_ids=edges,delay=floor),floor_integer=floor,proxy_budget_integer=budget,budget_integer=budget);witnesses[str(q['sink'])]=edges
 clip=max(dist[t] for t in targets);p=D/f'certificates/source_{source}.json'
 with p.open('x') as f:json.dump(dict(source=source,clip=clip,potentials={n:v for n,v in dist.items() if v<clip},witnesses=witnesses),f,separators=(',',':'));f.write('\n')
 certificates.append(dict(path=str(p),sha256=sha(p)))
records=[];owners=defaultdict(set);parents=defaultdict(dict);slots={eid:s for s,eid in enumerate(fields['edge_ids'])}
for q in sorted(queries,key=lambda q:q['connection_id']):
 cid=q['connection_id'];rec=fresh[cid] if q['net_id'] in dirty else oldrecords[cid];assert all(rec[k]==v for k,v in q.items());records.append(rec);net=q['net_id'];u=q['source'];owners[net].add(u)
 for eid in rec['answer']['physical_edge_ids']:
  slot=slots[eid];assert fields['row_offsets'][u]<=slot<fields['row_offsets'][u+1];v=fields['dest_ranks'][slot];edge=(u,fields['switch_ids'][slot])
  if nodes[v].get('type')!='SINK':
   assert v not in parents[net] or parents[net][v]==edge;parents[net][v]=edge
  owners[net].add(v);u=v
 assert u==q['sink'] and rec['answer']['delay']<=rec['budget_integer']
occupancy=Counter(n for used in owners.values() for n in used);overflow=sum(max(0,v-fields['capacities'][n]) for n,v in occupancy.items());frame=dict(prior,records=records,ledger=dict(occupancy),history={},epochs={n:int(n in dirty) for n in owners},overflow_units=overflow,scope='Staged placement prediction, may be congested, not native accepted route. Unchanged native paths and heuristic budgets preserved.')
with (D/'initial.json').open('x') as f:json.dump(frame,f);f.write('\n')
files=[Path(__file__),base/'initial.json',base/'independent_xml_verification_v1.json',targetroot/'staged_input_verification_v1.json',oldpath,ep,D/'initial.json'];bindings={str(p):sha(p) for p in files};bindings.update({v['path']:v['sha256'] for v in new['inputs'].values()});assert all(sha(p)==h for p,h in bindings.items())
with (D/'receipt.json').open('x') as f:json.dump(dict(bindings=bindings,affected=delta,certificates=certificates,recomputed_connections=len(fresh),preserved_native_connections=len(records)-len(fresh),source_search_calls=len(groups),overflow_units=overflow,stage_seconds_before_receipt=time.perf_counter()-start,scope='Dirty-only floor searches, complete new frame/ledger; previous bootstrap authenticated and paid separately. Independent XML proof of new state and feedback/native comparison pending.'),f,indent=2);f.write('\n')
print('STAGED recomputed',len(fresh),'preserved',len(records)-len(fresh),'overflow',overflow,flush=True)
