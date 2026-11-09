"""Compare instrumented native search ABI/output to frozen binary on fixtures."""
import ctypes,json,random,time
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'experiments/mux_old_priority_repair_2026-10-06/search.so'
new=ROOT/'experiments/mux_native_phase_profile_2026-10-06/search.so'
Q=ctypes.c_uint64;P=ctypes.POINTER(Q)
a,b=ctypes.CDLL(str(old)),ctypes.CDLL(str(new))
for lib in (a,b):lib.rc_query.argtypes=[Q,*([P]*7),*([Q]*7),P,P];lib.rc_query.restype=ctypes.c_int
b.rc_last_phase_ns.argtypes=[P];b.rc_last_phase_ns.restype=None
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
 for trial in range(10):
  source,sink=rng.randrange(n),rng.randrange(n);budget=rng.randrange(0,100);limit=rng.randrange(1,40)
  results=[]
  for lib in (a,b):
   path=(Q*limit)();out=(Q*8)();code=lib.rc_query(n,*arrays,source,sink,0,0,budget,0,limit,path,out)
   results.append((code,list(out),list(path[:out[3]]) if code==0 else []))
  assert results[0]==results[1]
  times=(Q*4)();b.rc_last_phase_ns(times);assert times[3]==0
  statuses[results[0][0]]=statuses.get(results[0][0],0)+1;total+=1
out=ROOT/'experiments/mux_native_phase_profile_2026-10-06/fixture_verification.json'
out.write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),old_binary_sha256=sha(old),new_binary_sha256=sha(new),native_source_sha256=sha(new.with_suffix('.cpp')),queries=total,statuses=statuses,scope='100 random graph fixtures/1000 calls: exact status, all8 output counters/cost/delay/path length and raw edge path equality. Native timer spare slot zero. Does not prove realistic full reroute parity/performance or every error contract.'),indent=2)+'\n');print(total,statuses)
