"""Explicit early rejection and uint128 overflow parity for timed native ABI."""
import ctypes,json
from pathlib import Path
from pre_route_endpoints import sha
from owned_reverse_graph import OwnedReverseGraph
ROOT=Path(__file__).resolve().parents[1];old=ROOT/'experiments/mux_old_priority_repair_2026-10-06/search.so';new=ROOT/'experiments/mux_owned_bound_cache_2026-10-06/search.so'
Q=ctypes.c_uint64;P=ctypes.POINTER(Q);baseline=ctypes.CDLL(str(old))
baseline.rc_query.argtypes=[Q,*([P]*7),*([Q]*7),P,P];baseline.rc_query.restype=ctypes.c_int
M=(1<<64)-1
cases=[('invalid_source',[0,1,2,2],[1,2],[2,2],[1,1],[1,1,1],[0,0,0],3,2,10,10,4),('zero_limit',[0,1,2,2],[1,2],[2,2],[1,1],[1,1,1],[0,0,0],0,2,10,0,4),('invalid_destination',[0,1,2,2],[3,2],[2,2],[1,1],[1,1,1],[0,0,0],0,2,10,10,4),('invalid_cost',[0,1,2,2],[1,2],[0,2],[1,1],[1,1,1],[0,0,0],0,2,10,10,4),('overflow',[0,1,2,2],[1,2],[M-1,M-1],[1,1],[M,M,M],[0,M-2,M-2],0,2,(1<<128)-1,10,3)]
rows=[]
for name,csr,dest,cost,inc,capacity,other,source,sink,budget,limit,expected in cases:
 arrays=[(Q*len(v))(*v) for v in (csr,dest,list(range(len(dest))),cost,capacity,inc,other)];results=[]
 path=(Q*max(1,limit))();out=(Q*8)();code=baseline.rc_query(3,*arrays,source,sink,0,0,budget&M,budget>>64,limit,path,out);results.append((code,list(out)))
 try:graph=OwnedReverseGraph(3,len(dest),arrays[0],arrays[1],arrays[2],arrays[5],new)
 except ValueError:
  assert name=='invalid_destination';results.append((4,[0]*8))
 else:
  path=(Q*max(1,limit))();out=(Q*8)();code=graph.bridge(3,*arrays,source,sink,0,0,budget&M,budget>>64,limit,path,out);results.append((code,list(out)));graph.close()
 assert results[0]==results[1] and results[0][0]==expected,(name,results)
 rows.append(dict(case=name,status=expected))
(new.parent/'error_verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),old_binary_sha256=sha(old),new_binary_sha256=sha(new),rows=rows,scope='Five explicit rejection/uint128 arithmetic parity fixtures; invalid graph rejected at owned creation boundary, valid graph query errors match raw query output; no allocation-failure injection or complete error-contract coverage.'),indent=2)+'\n');print(rows)
