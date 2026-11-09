"""Independent simple-path oracle for target pruning, including zero-cost cycles."""
import pathlib,json,hashlib,ctypes as C,random
from array import array
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/native_bounded_wire_target_prune_core_v2_2026-10-19';U=C.c_uint64;P=C.POINTER(U)
class Result(C.Structure):_fields_=[(k,U) for k in ['status','cost','delay','created','expanded','examined','path_size']]
def pointer(a,ctype=U):return C.cast(a.buffer_info()[0],C.POINTER(ctype))
def library(path):
 lib=C.CDLL(str(path));lib.rc_create.argtypes=[U,U]+[P]*7;lib.rc_create.restype=C.c_void_p;lib.rc_destroy.argtypes=[C.c_void_p];lib.rc_query.argtypes=[C.c_void_p]+[U]*6+[P,C.POINTER(C.c_uint8),P,P,C.POINTER(Result)];lib.rc_query.restype=C.c_int;lib.rc_copy_path.argtypes=[C.c_void_p,P,U];lib.rc_copy_path.restype=C.c_int;return lib

def main():
 O.mkdir(exist_ok=False);paths=[R/'build/native_bounded_wire_search_v1_2026-10-08/libroutecast_bounded.so',R/'build/native_bounded_wire_target_prune_v2_2026-10-19/libroutecast_bounded.so'];libs=[library(p) for p in paths];rng=random.Random(191023);found=0;absent=0;limited=0;enumerated=0;full_label_delta=0
 for fixture in range(500):
  n=rng.randrange(3,9);src=0;sink=n-1;row=array('Q',[0]);dest=array('Q');sw=array('Q');inc=array('Q');adj=[[] for _ in range(n)]
  for a in range(n):
   for b in range(n):
    if a!=b and (rng.random()<.3 or (fixture%2==0 and b==a+1)):
     eid=len(dest);dest.append(b);sw.append(rng.randrange(3));inc.append(rng.randrange(5));adj[a].append(eid)
   row.append(len(dest))
  eid=array('Q',range(len(dest)));cap=array('Q',(rng.randrange(1,3) for _ in range(n)));length=array('Q',(rng.randrange(5) for _ in range(n)));outside=array('Q',(0 if fixture%2==0 else rng.randrange(cap[v]+1) for v in range(n)));kept=array('B',(rng.randrange(2) for _ in range(n)));ps=array('Q',[0])*n;pw=array('Q',[0])*n
  if fixture%2:
   for v in range(n):
    if rng.random()<.25:ps[v]=rng.randrange(n)+1;pw[v]=rng.randrange(3)+1
  initial=rng.randrange(4);budget=initial+20 if fixture%2==0 else rng.randrange(20);bound=rng.randrange(1,15);oracle=[]
  def dfs(a,seen,cost,delay,route):
   nonlocal enumerated
   if delay>budget or cost>=bound:return
   if a==sink:oracle.append(((cost,delay),tuple(route)));enumerated+=1;return
   for e in adj[a]:
    b=dest[e]
    if b in seen or outside[b]>=cap[b] or (ps[b] and (ps[b]!=a+1 or pw[b]!=sw[e]+1)):continue
    dfs(b,seen|{b},cost+(0 if kept[b] else length[b]),delay+inc[e],route+[e])
  dfs(src,{src},0,initial,[]);best=min((value for value,_ in oracle),default=None);found+=best is not None;absent+=best is None;handles=[]
  try:
   for lib in libs:
    h=lib.rc_create(n,len(dest),*(pointer(x) for x in [row,dest,eid,sw,inc,cap,length]));assert h;handles.append(h)
   outputs=[]
   for lib,h in zip(libs,handles):
    out=Result();assert lib.rc_query(h,src,sink,initial,budget,bound,100000,pointer(outside),pointer(kept,C.c_uint8),pointer(ps),pointer(pw),C.byref(out))==0;assert out.status==(0 if best is not None else 1)
    if best is not None:
     assert (out.cost,out.delay)==best;buf=array('Q',[0])*max(1,out.path_size);assert lib.rc_copy_path(h,pointer(buf),out.path_size)==0;assert ((out.cost,out.delay),tuple(buf[:out.path_size])) in oracle
    outputs.append(out)
   full_label_delta+=outputs[0].created-outputs[1].created
   out=Result();assert libs[1].rc_query(handles[1],src,sink,initial,budget,bound,1,pointer(outside),pointer(kept,C.c_uint8),pointer(ps),pointer(pw),C.byref(out))==0;assert out.created<=1
   if out.status==0:assert (out.cost,out.delay)==best
   elif out.status==1:assert best is None
   else:assert out.status==2;limited+=1
  finally:
   for lib,h in zip(libs,handles):lib.rc_destroy(h)
 proof=R/'build/native_bounded_wire_target_prune_v2_2026-10-19/receipt.json';build=json.loads(proof.read_text())
 for path,h in build['bindings'].items():assert hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()==h
 out=dict(status='TARGET_REACHABILITY_PRUNING_MATCHES_INDEPENDENT_SIMPLE_PATH_OPTIMA',graphs=500,feasible=found,infeasible=absent,enumerated_budget_paths=enumerated,limited_unknown_queries=limited,sum_created_label_reduction=full_label_delta,source_RC_and_fixed_parent_and_capacity_and_zero_cost_cycle_cases=True,unchanged_Pareto_label_cap_semantics=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths+[proof,pathlib.Path(__file__).resolve()]},scope='Small exact finite directed graphs only. Reverse CSR construction and per-query reachability costs are additional measured work, not included in Pareto label counter. Actual MMC paired replay remains pending.')
 (O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
