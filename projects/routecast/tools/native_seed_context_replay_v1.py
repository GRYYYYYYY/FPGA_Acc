"""Strict binary actual route-tree seed push stream joined to schema2 attempts."""
import struct
from collections import Counter
MAX=2**64-1
class SeedError(ValueError):pass
class SeedStream:
 def __init__(self,path,nodes=904438):
  self.f=open(path,'rb');self.nodes=nodes;self.records=self.inside=self.outside=self.lastseq=0;self.done=False
  if self.f.readline()!=b'RC_SEED_PUSH_LE64 1\n':self.f.close();raise SeedError('header')
 def next(self):
  if self.done:return None
  b=self.f.read(32)
  if len(b)!=32:raise SeedError('truncated record/footer')
  seq,node,target,push=struct.unpack('<QQQQ',b)
  if seq==MAX:
   if (node,target,push)!=(self.records,self.inside,self.outside) or self.f.read(1):raise SeedError('footer totals or trailing data')
   self.done=True;self.f.close();return None
  if node>=self.nodes or target>=self.nodes or not push:raise SeedError('node/target/counter bounds')
  if seq:
   if seq<self.lastseq:raise SeedError('attempt sequence decreased')
   self.lastseq=seq;self.inside+=1
  else:self.outside+=1
  self.records+=1;return seq,node,target,push
 def close(self):self.f.close()
def replay(seed_path,connection_path,emit=None):
 stream=SeedStream(seed_path);record=stream.next();pending=None;rows=records=0;with_zero=0;maxseeds=0;last_attempt=0;ended=False
 def skip_outside(record):
  while record is not None and record[0]==0:record=stream.next()
  return record
 try:
  with open(connection_path) as f:
   if next(f)!='CONNECTION_TRACE 2\n':raise SeedError('connection header')
   for line in f:
    if ended:raise SeedError('connection trailing content')
    t=line.split()
    if t[0]=='A':
     if pending is not None:raise SeedError('pending attempt')
     pending=list(map(int,t[1:]));seq,it,net,pin,source,sink,before_push,before_pop=pending
     if seq!=last_attempt+1:raise SeedError('connection attempt sequence')
     last_attempt=seq
    elif t[0] in ('C','F'):
     v=list(map(int,t[1:]));
     if pending is None or v[:4]!=pending[:4]:raise SeedError('result identity')
     seq,it,net,pin,source,sink,before_push,before_pop=pending;after_push,after_pop=v[4:];count=0;nodes=set();previous=before_push;record=skip_outside(record)
     if record is not None and record[0]<seq:raise SeedError('orphan seed attempt')
     while record is not None and record[0]==seq:
      _,node,target,push=record
      if target!=sink or not previous<push<=after_push:raise SeedError('seed target or heap counter outside attempt')
      previous=push;nodes.add(node);count+=1;record=skip_outside(stream.next())
     if count>after_push-before_push or after_pop<before_pop:raise SeedError('work bounds')
     row=dict(sequence=seq,iteration=it,native_NET=net,native_pin=pin,source_RR=source,sink_RR=sink,seed_heap_pushes=count,unique_seed_RRs=len(nodes),all_heap_pushes=after_push-before_push,all_heap_pops=after_pop-before_pop,result=t[0]);rows+=1;records+=count;with_zero+=count==0;maxseeds=max(maxseeds,count)
     if emit is not None:emit(row)
     pending=None
    elif t[0]=='END':
     if pending is not None or int(t[2])!=rows:raise SeedError('connection END')
     ended=True
  record=skip_outside(record)
  if not ended or record is not None or not stream.done or records!=stream.inside:raise SeedError('unconsumed seed data or connection truncation')
  return dict(attempts=rows,seed_records=stream.records,inside_seed_pushes=stream.inside,outside_seed_pushes=stream.outside,zero_seed_attempts=with_zero,max_seed_pushes_per_attempt=maxseeds,scope='Actual seed pushes over each sink call, including any internal fallback/retry. No setup-phase boundary recorded; cannot automatically treat union as initial prospective search frontier.')
 finally:stream.close()
