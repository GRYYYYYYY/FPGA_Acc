"""Synchronous graph/model-bound exact floor cache; no native route labels."""
import copy,json,struct,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from freeze_priority_family import closure

class ReusableRRFloors:
 def __init__(self,endpoint,binary,workspace):
  start=time.perf_counter();self.binary=Path(binary);self.workspace=Path(workspace);self.workspace.mkdir(exist_ok=False)
  self.graph,self.digest,nodes,self.fields,self.rc,_=load_endpoints(endpoint);self.n=len(nodes);self.initial=[self.rc.initial(u) for u in range(self.n)]
  assert max(self.initial)+self.n*max(self.rc.increments)<(1<<64)-1
  self.bindings=closure([Path(__file__)]);self.bindings[str(self.binary)]=sha(self.binary);self.bindings[str(self.graph)]=self.digest
  self.model_digest=sha(Path(__file__)) # Full dependency/binary hashes also bound and checked.
  self.graph_bytes=b''.join(struct.pack('<Q',v) for a in (self.fields['row_offsets'],self.fields['dest_ranks'],self.rc.increments,self.fields['capacities'],self.initial) for v in a)
  self._cache={};self.epoch=0;self.construction_seconds=time.perf_counter()-start
 def _validate(self,endpoint):
  ep=Path(endpoint);digest=sha(ep);meta=json.loads(ep.read_text())
  if meta['graph_sha256']!=self.digest or meta['inputs']['graph']['sha256']!=self.digest:raise ValueError('graph identity mismatch')
  if not all(sha(f)==h for f,h in self.bindings.items()):raise ValueError('context graph/model/binary changed')
  if not all(sha(v['path'])==v['sha256'] for v in meta['inputs'].values()):raise ValueError('endpoint input changed')
  queries=meta['connections'];seen=set()
  for q in queries:
   if any(type(q[k]) is not int for k in ('connection_id','net_id','source','sink')):raise ValueError('integer identities required')
   cid=q['connection_id']
   if cid<0 or cid in seen or str(q['net_id']) not in meta['net_names']:raise ValueError('query identity')
   seen.add(cid)
   if any(v<0 or v>=self.n or self.fields['capacities'][v]<=0 for v in (q['source'],q['sink'])):raise ValueError('RR endpoint invalid')
  return meta,digest
 def query(self,endpoint):
  start=time.perf_counter();meta,endpoint_hash=self._validate(endpoint);validated=time.perf_counter();queries=meta['connections'];keys=[(self.digest,self.model_digest,q['source'],q['sink']) for q in queries]
  missing=sorted(set(keys)-set(self._cache));staged={};step=self.workspace/f'epoch_{self.epoch+1}';step.mkdir(exist_ok=False)
  if missing:
   payload=step/'queries.bin';nq=len(missing)
   header=struct.pack('<4Q',0x5243464c4f4f5231,self.n,len(self.fields['edge_ids']),nq)
   tail=b''.join(struct.pack('<3Q',i,key[2],key[3]) for i,key in enumerate(missing));payload.write_bytes(header+self.graph_bytes+tail)
   with (step/'output.jsonl').open('w') as stream:result=subprocess.run([str(self.binary),str(payload)],stdout=stream,stderr=subprocess.PIPE,timeout=120)
   if result.returncode:raise RuntimeError(result.stderr.decode())
   answers=[json.loads(line) for line in (step/'output.jsonl').read_text().splitlines()]
   if len(answers)!=nq or {a['connection_id'] for a in answers}!=set(range(nq)):raise ValueError('answer coverage')
   for a in answers:
    key=missing[a['connection_id']]
    if a['minimum_integer'] is None:raise ValueError('unreachable floor: no epoch/cache publication')
    edges=[self.fields['edge_ids'][slot] for slot in a['slots']]
    if self.rc.path(key[2],key[3],edges)!=a['minimum_integer']:raise ValueError('path mismatch')
    staged[key]=dict(minimum_integer=a['minimum_integer'],physical_edge_ids=edges)
  # Close input/model bindings before publication; callers must avoid concurrent writers.
  self._validate(endpoint)
  if sha(endpoint)!=endpoint_hash:raise ValueError('endpoint changed during query')
  answers=[dict(query=copy.deepcopy(q),**copy.deepcopy(staged.get(key,self._cache.get(key)))) for q,key in zip(queries,keys)]
  self._cache.update(staged);self.epoch+=1
  receipt=dict(epoch=self.epoch,endpoint_sha256=endpoint_hash,graph_sha256=self.digest,scale=self.rc.scale,required_connections=len(queries),unique_pairs=len(set(keys)),miss_pairs=len(missing),hit_connections=sum(key in self._cache and key not in staged for key in keys),cache_entries=len(self._cache),validation_seconds=validated-start,query_and_closing_validation_seconds=time.perf_counter()-validated,total_seconds=time.perf_counter()-start,answers=answers)
  (step/'receipt.json').write_text(json.dumps(receipt,separators=(',',':'))+'\n');return receipt
