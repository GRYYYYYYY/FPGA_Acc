"""Fresh Python feedback prices drive a resident VPR RRGraphView search service."""
import json,os,socket,subprocess,tempfile,time,shutil
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
class Search:
 def __init__(self,f,rc,binary):
  self.f=f;self.rc=rc;self.slots={e:i for i,e in enumerate(f['edge_ids'])};self.phase=-1;self.used=set();self.keys={};self.closed=False
  self.work=Path(os.environ['ROUTECAST_LIVE_WORK']).resolve();self.work.mkdir();self.bindings={}
  ep=Path(os.environ['ROUTECAST_LIVE_ENDPOINT']).resolve()
  from class_cached_rc_endpoint_context_v1 import load_endpoints
  _,_,_,original,_,queries=load_endpoints(ep)
  assert all(f[k]==original[k] for k in ['edge_ids','row_offsets','dest_ranks','capacities'])
  manifest=R/'experiments/native_inprocess_forward_prepare_v1_2026-10-10/queries.txt';cidnet={}
  for l in manifest.read_text().splitlines():
   x=l.split()
   if x[0]=='Q':cidnet[int(x[1])]=int(x[2])
  groups=defaultdict(list)
  for q in queries:groups[q['net_id']].append(q)
  for qs in groups.values():
   key=(qs[0]['source'],frozenset(q['sink'] for q in qs));assert key not in self.keys;nativeids={cidnet[q['connection_id']] for q in qs};assert len(nativeids)==1;self.keys[key]=(next(iter(nativeids)),qs)
  B=R/'build/native_live_search_service_v1_2026-10-10';bp=B/'receipt.json';b=json.loads(bp.read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['bindings'].items()) and all(sha(p)==h for p,h in b['source_sha256'].items())
  source=R/'experiments/sha_second_swap_overflow_guard_complete_workflow_v1_2026-10-10/cold/native/sha1';rp=source/'receipt.json';r=json.loads(rp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items()) and all(sha(p)==h for p,h in r['files'].items())
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(source/name,self.work/name)
  self.bindings={str(p):sha(p) for p in [ep,manifest,bp,rp,B/'sequence_vpr',Path(__file__).resolve(),*(self.work/n for n in ['design.blif','design.net','design.place'])]}
  self.tmp=tempfile.TemporaryDirectory(prefix='rc-live-');path=str(Path(self.tmp.name)/'rpc');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_INPROCESS_QUERIES=str(manifest),ROUTECAST_INPROCESS_FLOORS=str(self.work/'unused.tsv'),ROUTECAST_LIVE_SOCKET=path)
  command=r['command'].copy();command[0]=str(B/'sequence_vpr');self.log=(self.work/'native.log').open('w');self.transcript=(self.work/'wire.jsonl').open('w');self.start=time.perf_counter();self.proc=subprocess.Popen(command,cwd=self.work,env=env,stdout=self.log,stderr=subprocess.STDOUT);self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.sock.settimeout(30)
  until=time.monotonic()+30
  while True:
   try:self.sock.connect(path);break
   except (FileNotFoundError,ConnectionRefusedError):
    if self.proc.poll() is not None or time.monotonic()>until:raise RuntimeError('native startup failed/timed out')
    time.sleep(.02)
  self.reader=self.sock.makefile('r');assert self.read()==f'READY\t{len(groups)}\t6273';self.calls=[]
 def read(self):
  l=self.reader.readline()
  if not l:raise RuntimeError('native response disconnected')
  l=l.rstrip('\n');self.transcript.write(json.dumps(dict(receive=l))+'\n');return l
 def send(self,text):
  self.transcript.write(json.dumps(dict(send=text))+'\n');self.sock.sendall(text.encode())
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
  if self.closed:return
  self.send('O\n');assert self.read()==f"DONE\t{sum(c['connections'] for c in self.calls)}";self.reader.close();self.sock.close();code=self.proc.wait(timeout=30);self.log.close();self.transcript.close();self.tmp.cleanup();assert code==0
  assert all(sha(p)==h for p,h in self.bindings.items());assert 'VPR succeeded' in (self.work/'native.log').read_text();self.closed=True
  (self.work/'receipt.json').write_text(json.dumps(dict(bindings=self.bindings,exit_code=code,calls=self.calls,native_with_controller_seconds=time.perf_counter()-self.start,files={str(p):sha(p) for p in self.work.iterdir() if p.is_file()},scope='Fresh dynamic prices sent to live resident native RR search. Python owns fallback/estimate ledger/epochs; native actual route state unmodified. Native clock includes controller computation and serialization; not standalone search time.'),indent=2)+'\n')
