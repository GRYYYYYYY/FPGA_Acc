"""Owned snapshot lifetime and mutable-cost rejection boundaries."""
import ctypes,json
from pathlib import Path
from owned_reverse_graph import OwnedReverseGraph
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];lib=ROOT/'experiments/mux_owned_bound_cache_2026-10-06/search.so';Q=ctypes.c_uint64
rows=(Q*3)(0,1,1);dest=(Q*1)(1);edges=(Q*1)(17);inc=(Q*1)(3)
g=OwnedReverseGraph(2,1,rows,dest,edges,inc,lib)
cost=(Q*1)(3);capacity=(Q*2)(1,1);other=(Q*2)(0,0)
def query():
 path=(Q*10)();out=(Q*8)();code=g.lib.rc_graph_query(g.handle,cost,capacity,other,0,1,0,0,10,0,10,path,out)
 return code,list(out),list(path[:out[3]]) if code==0 else []
before=query();assert before[0]==0 and before[2]==[17]
rows[1]=0;dest[0]=0;edges[0]=99;inc[0]=9
assert query()==before # Original graph arrays are no longer owned/read.
cost[0]=2;assert query()[0]==4
cost[0]=(1<<64)-1;assert query()[0]==1
cost[0]=3;assert query()==before
h=g.handle;g.close();assert query()[0]==4 and g.lib.rc_graph_destroy(h)==4
g.close() # Python close is explicitly idempotent.
for bad_rows,bad_dest in [([0,2,1],[1]),([0,1,1],[2])]:
 try:OwnedReverseGraph(2,1,(Q*3)(*bad_rows),(Q*1)(*bad_dest),(Q*1)(17),(Q*1)(3),lib)
 except ValueError:pass
 else:raise AssertionError('invalid CSR accepted')
(lib.parent/'contract_verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),wrapper_sha256=sha(ROOT/'tools/owned_reverse_graph.py'),binary_sha256=sha(lib),checks=['owned_copy_after_input_mutation','dynamic_cost_rejection','sentinel_disable_and_restore','closed_handle','repeated_destroy_rejection','idempotent_close','invalid_rows','invalid_destination'],scope='Explicit owned context API contract; graph mutations after creation intentionally do not change snapshot. Dynamic demand/cost remain query-local. No borrowed-pointer cache or raw stateless graph mutation parity claim.'),indent=2)+'\n');print('owned graph contract passed')
