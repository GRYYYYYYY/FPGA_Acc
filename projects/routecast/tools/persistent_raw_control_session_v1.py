"""Serial raw baseline with paid reusable RR/RC and native path import.

No criticality workspace, old floor cache or local feedback metadata is loaded.
The source generation is replaced only by constructing a new session.
"""
import json,time,heapq
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete

class Session:
 def __init__(self,endpoint,route):
  tick=time.perf_counter();self.closed=False;self.active=False;self.generation=0
  self.sources=closure([Path(__file__)])
  self.source_endpoint=Path(endpoint).resolve();self.source_hash=sha(self.source_endpoint)
  self.old=json.loads(self.source_endpoint.read_text());self.route=Path(route).resolve();self.route_hash=sha(self.route)
  self.graph,self.digest,self.nodes,self.fields,self.rc,queries=load_endpoints(self.source_endpoint)
  self.state,rows,self.ledger=load_complete(self.route,self.old,self.nodes,self.fields,self.rc)
  self.nativerows={r['connection_id']:{**r,'physical_edge_ids':tuple(r['physical_edge_ids'])} for r in rows}
  self.oldq={q['connection_id']:q for q in queries}
  self.cold_seconds=time.perf_counter()-tick;self.calls=0
 def predict(self,endpoint,output,*,generation):
  tick=time.perf_counter()
  if self.closed or self.active or type(generation) is not int or generation!=self.generation:raise RuntimeError('closed, active or stale raw source')
  endpoint=Path(endpoint).resolve();before=sha(endpoint);new=json.loads(endpoint.read_text())
  if not all(sha(p)==h for p,h in self.sources.items()):raise ValueError('raw source implementation changed')
  if sha(self.route)!=self.route_hash or sha(self.source_endpoint)!=self.source_hash:raise ValueError('raw native source changed')
  if new['graph_sha256']!=self.digest or new['inputs']['graph']['sha256']!=self.digest or sha(self.graph)!=self.digest:raise ValueError('graph epoch changed')
  if new['inputs']['net']['sha256']!=self.old['inputs']['net']['sha256'] or new['net_names']!=self.old['net_names']:raise ValueError('netlist epoch changed')
  if not all(sha(v['path'])==v['sha256'] for v in new['inputs'].values()):raise ValueError('endpoint input changed')
  queries=new['connections'];byid={q['connection_id']:q for q in queries}
  if len(byid)!=len(queries) or set(byid)!=set(self.oldq):raise ValueError('raw CID coverage')
  for cid,q in byid.items():
   if type(cid) is not int or q['net_id']!=self.oldq[cid]['net_id']:raise ValueError('raw CID/NET identity')
   for key,kind in [('source','SOURCE'),('sink','SINK')]:
    n=q[key]
    if type(n) is not int or not 0<=n<len(self.nodes) or self.nodes[n].get('type')!=kind:raise ValueError('invalid endpoint')
  if sha(endpoint)!=before:raise ValueError('endpoint changed during bind')
  dirty={q['net_id'] for cid,q in byid.items() if (q['source'],q['sink'])!=(self.oldq[cid]['source'],self.oldq[cid]['sink'])}
  D=Path(output).resolve();D.mkdir(exist_ok=False);(D/'certificates').mkdir()
  fields=self.fields;rc=self.rc;nodes=self.nodes;oldq=self.oldq;nativerows=self.nativerows;groups=defaultdict(list)
  for q in queries:
   if q['net_id'] in dirty:groups[q['source']].append(q)
  self.request_bindings={v['path']:v['sha256'] for v in new['inputs'].values()}
  self.active=True
  try:return self._execute(D,queries,fields,rc,nodes,oldq,nativerows,groups,dirty,tick,endpoint,before)
  finally:self.active=False
 def _execute(self,D,queries,fields,rc,nodes,oldq,nativerows,groups,dirty,tick,endpoint,endpoint_hash):
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

  if sha(endpoint)!=endpoint_hash or sha(self.route)!=self.route_hash:raise ValueError('raw inputs changed during execution')
  self.calls+=1
  result=dict(source_generation=self.generation,calls=self.calls,total_call_seconds=time.perf_counter()-tick,dirty_search_and_certificates_seconds=search_seconds,dirty_nets=sorted(dirty),recomputed_connections=len(fresh),preserved_connections=len(records)-len(fresh),source_searches=len(groups),overflow_units=overflow,certificates=certs,bindings={**self.sources,**self.request_bindings,str(endpoint):endpoint_hash,str(self.source_endpoint):self.source_hash,str(self.route):self.route_hash})
  if not all(sha(p)==h for p,h in result['bindings'].items()):raise ValueError('raw bindings changed during execution')
  with (D/'receipt.json').open('x') as f:json.dump(result,f,indent=2)
  return result
 def close(self):
  self.closed=True;self.active=False
