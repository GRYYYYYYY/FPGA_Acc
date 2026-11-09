"""Compare instrumented native search ABI/output to frozen binary on fixtures."""
import ctypes,json,random,time
from owned_reverse_graph import OwnedReverseGraph
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'experiments/mux_old_priority_repair_2026-10-06/search.so'
new=ROOT/'experiments/mux_owned_reverse_graph_2026-10-06/search.so'
Q=ctypes.c_uint64;P=ctypes.POINTER(Q)
a=ctypes.CDLL(str(old))
a.rc_query.argtypes=[Q,*([P]*7),*([Q]*7),P,P];a.rc_query.restype=ctypes.c_int
rng=random.Random(17251);statuses={};total=0
for fixture in range(100):
 n=rng.randrange(3,31);rows=[0];dest=[];edge=[];cost=[];inc=[]
 for u in range(n):
  for v in range(n):
   if u!=v and rng.random()<.1:
    dest.append(v);edge.append(len(edge));increment=rng.randrange(1,20);inc.append(increment);cost.append(increment*rng.randrange(1,4))
  rows.append(len(dest))
 capacity=[rng.randrange(0,3) for _ in range(n)];other=[rng.randrange(0,3) for _ in range(n)]
 arrays=[(Q*len(x))(*x) for x in (rows,dest,edge,cost,capacity,inc,other)]
 graph=OwnedReverseGraph(n,len(dest),arrays[0],arrays[1],arrays[2],arrays[5],new)
 class Adapter:pass
 b=Adapter();b.rc_query=graph.bridge
 for trial in range(10):
  for slot in range(len(dest)):
   arrays[3][slot]=(1<<64)-1 if rng.random()<.15 else inc[slot]*rng.randrange(1,4)
  source,sink=rng.randrange(n),rng.randrange(n);budget=rng.randrange(0,100);limit=rng.randrange(1,40)
  results=[]
  for lib in (a,b):
   path=(Q*limit)();out=(Q*8)();code=lib.rc_query(n,*arrays,source,sink,0,0,budget,0,limit,path,out)
   results.append((code,list(out),list(path[:out[3]]) if code==0 else []))
  assert results[0]==results[1]

  statuses[results[0][0]]=statuses.get(results[0][0],0)+1;total+=1
 graph.close()
 # Destroyed handle must reject all later queries and repeated destruction.
 result=(Q*8)(*([9]*8));path=(Q*10)()
 assert graph.bridge(n,*arrays,0,0,0,0,10,0,10,path,result)==4 and list(result)==[0]*8
out=ROOT/'experiments/mux_owned_reverse_graph_2026-10-06/fixture_verification.json'
out.write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),old_binary_sha256=sha(old),new_binary_sha256=sha(new),native_source_sha256=sha(new.with_suffix('.cpp')),queries=total,statuses=statuses,scope='100 random graph fixtures/1000 calls: exact status, all8 output counters/cost/delay/path length and raw edge path equality. Dynamic UINT64_MAX edge-mask changes validated every query; closed handles rejected with zero output. Does not prove realistic full reroute parity/performance or every error contract.'),indent=2)+'\n');print(total,statuses)
