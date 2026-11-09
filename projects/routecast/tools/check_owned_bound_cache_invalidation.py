"""Explicit bounded-cache hits, exact mask invalidation and rejection recovery."""
import ctypes,json
from pathlib import Path
from owned_reverse_graph import OwnedReverseGraph
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];file=ROOT/'experiments/mux_owned_bound_cache_2026-10-06/search.so';Q=ctypes.c_uint64;P=ctypes.POINTER(Q)
arrays=[(Q*len(x))(*x) for x in ([0,1,2,2],[1,2],[7,8],[2,2],[1,1,1],[1,1],[0,0,0])]
original=ctypes.CDLL(str(ROOT/'experiments/mux_old_priority_repair_2026-10-06/search.so'));original.rc_query.argtypes=[Q,*([P]*7),*([Q]*7),P,P];original.rc_query.restype=ctypes.c_int
g=OwnedReverseGraph(3,2,arrays[0],arrays[1],arrays[2],arrays[5],file)
g.lib.rc_graph_cache_config.argtypes=[Q,Q];g.lib.rc_graph_cache_config.restype=ctypes.c_int
g.lib.rc_graph_cache_stats.argtypes=[Q,P];g.lib.rc_graph_cache_stats.restype=ctypes.c_int
assert g.lib.rc_graph_cache_config(g.handle,48)==0
checks=[]
def stats():
 out=(Q*6)();assert g.lib.rc_graph_cache_stats(g.handle,out)==0
 assert out[4]<=out[5];return list(out)
def query(sink=2):
 results=[]
 for callback in (original.rc_query,g.bridge):
  path=(Q*10)();out=(Q*8)();code=callback(3,*arrays,0,sink,0,0,10,0,10,path,out)
  results.append((code,list(out),list(path[:out[3]]) if code==0 else []))
 assert results[0]==results[1];checks.append(results[0][0]);return results[0][0]
query();assert stats()[:2]==[0,1]
query();assert stats()[:2]==[1,1]
arrays[3][0]=3;query();assert stats()[:2]==[2,1] # Weight change doesn't change relaxed delay bound.
query(1);assert stats()[3]==1 # One vector fits, LRU eviction.
query();assert stats()[3]==2
arrays[3][0]=(1<<64)-1;assert query()==1;assert stats()[2]==1
arrays[3][0]=2;query();assert stats()[2]==2
before=stats();arrays[3][0]=0;arrays[3][1]=(1<<64)-1;assert query()==4;assert stats()==before
arrays[3][0]=2;arrays[3][1]=2;query();assert stats()[0]==before[0]+1
assert g.lib.rc_graph_cache_config(g.handle,0)==0 and stats()[4]==0
before=stats();query();query();assert stats()[0]==before[0] and stats()[1]==before[1]+2 and stats()[4]==0
h=g.handle;g.close();assert g.lib.rc_graph_cache_config(h,48)==4
(file.parent/'cache_verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),binary_sha256=sha(file),checks=len(checks),scope='Exact raw-search parity across cache hits, cost-only updates, one-vector LRU eviction, disable/re-enable mask invalidation, invalid-cost-before-mask rejection preserving cache, zero-budget uncached queries and stale-handle config rejection. Payload bound applies only cached lowerbound vectors; owned graph/mask/LRU metadata and transient active vectors additional.'),indent=2)+'\n');print('cache invalidation/eviction contract passed',len(checks))
