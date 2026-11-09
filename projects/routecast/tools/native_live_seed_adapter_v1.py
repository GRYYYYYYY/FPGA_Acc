"""Fresh Python feedback prices drive a resident VPR RRGraphView search service."""
import json,os,socket,subprocess,tempfile,time,shutil
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
ACTIVE=None
class Search:
 def __init__(self,f,rc,binary):
  self.f=f;self.rc=rc;self.slots={e:i for i,e in enumerate(f['edge_ids'])};self.phase=-1;self.used=set();self.keys={};self.closed=False
  self.work=Path(os.environ['ROUTECAST_LIVE_WORK']).resolve();self.work.mkdir(exist_ok=True);assert not (self.work/'output.route').exists();self.bindings={}
  ep=Path(os.environ['ROUTECAST_LIVE_ENDPOINT']).resolve()
  epdata=json.loads(ep.read_text());assert all(sha(v['path'])==v['sha256'] for v in epdata['inputs'].values());queries=epdata['connections']
  from prepare_live_native_manifest_v1 import prepare
  manifest=self.work/'queries.txt';cidnet=prepare(ep,manifest)
  groups=defaultdict(list)
  for q in queries:groups[q['net_id']].append(q)
  for qs in groups.values():
   key=(qs[0]['source'],frozenset(q['sink'] for q in qs));assert key not in self.keys;nativeids={cidnet[q['connection_id']] for q in qs};assert len(nativeids)==1;self.keys[key]=(next(iter(nativeids)),qs)
  B=R/'build/native_live_seed_service_v1_2026-10-10';bp=B/'receipt.json';b=json.loads(bp.read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['bindings'].items()) and all(sha(p)==h for p,h in b['source_sha256'].items())
  source=Path(epdata['inputs']['net']['path']).parent;arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';graph=Path(epdata['inputs']['graph']['path'])
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(source/name,self.work/name)
  self.bindings={str(p):sha(p) for p in [ep,manifest,bp,arch,graph,B/'sequence_vpr',Path(__file__).resolve(),*(self.work/n for n in ['design.blif','design.net','design.place'])]}
  command=[str(B/'sequence_vpr'),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
  request_read,request_write=os.pipe();response_read,response_write=os.pipe();env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_INPROCESS_QUERIES=str(manifest),ROUTECAST_INPROCESS_FLOORS=str(self.work/'unused.tsv'),ROUTECAST_LIVE_REQUEST_FD=str(request_read),ROUTECAST_LIVE_RESPONSE_FD=str(response_write))
  self.log=(self.work/'native.log').open('w');self.transcript=(self.work/'wire.jsonl').open('w');self.start=time.perf_counter();self.command=command;self.proc=subprocess.Popen(command,cwd=self.work,env=env,stdout=self.log,stderr=subprocess.STDOUT,pass_fds=(request_read,response_write));os.close(request_read);os.close(response_write)
  self.writer=os.fdopen(request_write,'w');self.reader=os.fdopen(response_read,'r');assert self.read()==f'READY\t{len(groups)}\t6273';self.calls=[]
 def read(self):
  l=self.reader.readline()
  if not l:raise RuntimeError('native response disconnected')
  l=l.rstrip('\n');self.transcript.write(json.dumps(dict(receive=l))+'\n');return l
 def send(self,text):
  self.transcript.write(json.dumps(dict(send=text))+'\n');self.writer.write(text);self.writer.flush()
 def prepare(self,prices,weight):
  self.phase+=1;assert self.phase<3 and weight==(0 if self.phase==0 else 50000000);self.used=set();assert all(isinstance(n,int) and 0<=n<len(self.f['capacities']) and isinstance(v,int) and 0<=v<2**64 for n,v in prices.items())
  self.send(f'P {len(prices)} {weight}\n'+''.join(f'{n} {v}\n' for n,v in sorted(prices.items())));assert self.read()==f'A\t{self.phase}'
 def search(self,source,sinks):
  key=(source,frozenset(sinks));assert key not in self.used;self.used.add(key);net,qs=self.keys[key];self.send(f'S {net}\n');observed={}
  for _ in qs:
   x=self.read().split();assert x[0]=='Q';cid,delay,count=map(int,x[1:4]);path=list(map(int,x[4:]));assert cid not in observed and count==len(path);observed[cid]=(delay,path)
  assert self.read()==f'Z\t{net}\t{len(qs)}';assert set(observed)=={q['connection_id'] for q in qs};parents={};raw={source:self.rc.initial(source)}
  for q in qs:
   delay,path=observed[q['connection_id']];u=source;seen={u}
   for eid in path:
    slot=self.slots[eid];assert self.f['row_offsets'][u]<=slot<self.f['row_offsets'][u+1];v=self.f['dest_ranks'][slot];assert v not in seen;seen.add(v);assert v not in parents or parents[v]==(u,slot);parents[v]=(u,slot);u=v
   assert u==q['sink'] and self.rc.path(source,u,path)==delay;assert u not in raw or raw[u]==delay;raw[u]=delay
  self.calls.append(dict(phase=self.phase,native_net=net,connections=len(qs)))
  return raw,parents,set(sinks)
 def close(self):
  global ACTIVE
  if self.closed:return
  if os.environ.get('ROUTECAST_LIVE_DEFER_SEED')=='1':ACTIVE=self;return
  self.finish()
 def finish(self,seed=None):
  tick=time.perf_counter()
  if seed is not None:
   seed=Path(seed).resolve();assert seed.is_file() and not any(c.isspace() for c in str(seed));self.bindings[str(seed)]=sha(seed)
  self.send('O\n' if seed is None else f'I {seed}\n');assert self.read()==f"DONE\t{sum(c['connections'] for c in self.calls)}";self.reader.close();self.writer.close();code=self.proc.wait(timeout=30);self.log.close();self.transcript.close();assert code==0
  assert all(sha(p)==h for p,h in self.bindings.items());assert 'VPR succeeded' in (self.work/'native.log').read_text();self.closed=True
  (self.work/'service_receipt.json').write_text(json.dumps(dict(bindings=self.bindings,exit_code=code,command=self.command,calls=self.calls,seed_imported=seed is not None,seed_resume_to_finish_seconds=time.perf_counter()-tick,native_with_controller_seconds=time.perf_counter()-self.start,files={str(p):sha(p) for p in self.work.iterdir() if p.is_file()},scope='Fresh dynamic prices sent to live resident native RR search. Python owns fallback/estimate ledger/epochs; audited seed imported into actual native route state in the same process after search. Native clock includes controller computation and serialization; not standalone search time.'),indent=2)+'\n')
