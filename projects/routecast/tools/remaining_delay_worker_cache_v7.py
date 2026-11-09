"""Sequential on-demand compiled bounds; original cache identity/FIFO/publication semantics."""
import struct,sys,time
from array import array
from pathlib import Path
from pre_route_endpoints import sha
from remaining_delay_session_cache_v5 import RemainingDelayCache as Reference,DelayView
from capped_bound_worker_client_v1 import BoundWorker
class RemainingDelayCache(Reference):
 def __init__(self,graph,digest,fields,rc,workspace,max_entries=64,binary=None):
  start=time.perf_counter();super().__init__(graph,digest,fields,rc,workspace,max_entries)
  self.binary=Path(binary) if binary is not None else Path(__file__).resolve().parents[1]/'build/capped_bound_worker_cpp_v2_2026-10-07/compute'
  self.worker_graph=self.workspace/'worker_graph.bin'
  with self.worker_graph.open('wb') as stream:
   stream.write(struct.pack('<3Q',2026100706,self.n,len(self.fields['edge_ids'])))
   for values in (self.fields['row_offsets'],self.fields['dest_ranks'],self.fields['capacities'],self.rc.increments):
    data=array('Q',values)
    if sys.byteorder!='little':data.byteswap()
    stream.write(data.tobytes())
  self._worker_assets={p:(self._asset_stat(p),sha(p)) for p in (self.binary,self.worker_graph)};self.worker=None;self.worker_restarts=0
  try:self.worker=BoundWorker(self.binary,self.worker_graph,self.n,self.cutoff);self._check_graph()
  except BaseException:
   if self.worker is not None:self.worker.abort()
   raise
  self.construction_seconds=time.perf_counter()-start
 @staticmethod
 def _asset_stat(path):
  s=path.stat();return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 def _check_graph(self):
  if self._closed or self._invalid:raise ValueError('cache session closed or invalid')
  try:
   super()._check_graph()
   for path,(stamp,digest) in getattr(self,'_worker_assets',{}).items():
    if self._asset_stat(path)!=stamp:raise ValueError('worker asset changed')
  except (OSError,ValueError):
   self._invalid=True
   if getattr(self,'worker',None) is not None:self.worker.abort()
   raise
 def get(self,sink,deadline=None):
  tick=time.perf_counter();self._check_graph()
  if type(sink) is not int or not 0<=sink<self.n or self.fields['capacities'][sink]<=0:raise ValueError('invalid sink')
  self.validation_seconds+=time.perf_counter()-tick
  if deadline is not None and time.perf_counter()>=deadline:self.aborted+=1;raise TimeoutError('bound request deadline')
  if sink in self.entries:self.hits+=1;return self.entries[sink]
  self.misses+=1;start=time.perf_counter()
  try:
   if self.worker.closed:
    self.worker=BoundWorker(self.binary,self.worker_graph,self.n,self.cutoff,timeout=30 if deadline is None else max(0,deadline-time.perf_counter()));self.worker_restarts+=1
   archive=self.worker.get(sink,deadline=deadline)
   if deadline is not None and time.perf_counter()>=deadline:raise TimeoutError('complete bound exceeded deadline')
   self._check_graph()
  except TimeoutError:
   self.aborted+=1;self.build_seconds+=time.perf_counter()-start;raise
  except BaseException:
   self._invalid=True;self.worker.abort();raise
  if sys.byteorder=='little':data=archive
  else:
   native=array('Q');native.frombytes(archive);native.byteswap();data=native.tobytes()
  file=self.workspace/f'miss{self.misses}_sink{sink}.bin';file.write_bytes(archive);view=DelayView(data)
  if len(self.entries)>=self.max_entries:del self.entries[next(iter(self.entries))];self.evictions+=1
  self.entries[sink]=view;elapsed=time.perf_counter()-start;self.build_seconds+=elapsed;self.events.append(dict(index=self.misses,sink=sink,sha256=sha(file),path=str(file),seconds=elapsed));return view
 def finalize(self):
  start=time.perf_counter()
  try:
   self._check_graph()
   for path,(stamp,digest) in self._worker_assets.items():
    if sha(path)!=digest:raise ValueError('closing worker asset digest mismatch')
   self.worker.close();return super().finalize()
  except BaseException:
   self._invalid=True;self.worker.abort();raise
  finally:self.worker_close_and_validation_seconds=time.perf_counter()-start
 def abort(self):
  self._invalid=True;self.worker.abort()
 def summary(self):
  result=super().summary();result.update(backend='on-demand C++ worker, sequential',worker_restarts=self.worker_restarts,worker_assets={str(p):digest for p,(stamp,digest) in self._worker_assets.items()},worker_closed=self.worker.closed,worker_close_and_validation_seconds=getattr(self,'worker_close_and_validation_seconds',0));return result
