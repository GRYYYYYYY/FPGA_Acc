"""Full traced/untraced requested-result parity and unread-price perturbations."""
from pathlib import Path
from types import SimpleNamespace
import random,ctypes as C,json,hashlib
from soft_demand_workspace_bridge_v1 import Search as Forward
from bidirectional_rc_bridge_v1 import Bidirectional
R=Path(__file__).resolve().parents[1];B=R/'build/price_read_trace_v1_2026-10-10';O=R/'experiments/price_read_trace_contract_v1_2026-10-10';O.mkdir(exist_ok=True)
def trace(s):
 s.lib.rc_reads_clear.restype=None;s.lib.rc_reads_count.restype=C.c_uint64;s.lib.rc_reads_at.argtypes=[C.c_uint64];s.lib.rc_reads_at.restype=C.c_uint64
 s.lib.rc_reads_clear()
def deps(s):return {s.lib.rc_reads_at(i) for i in range(s.lib.rc_reads_count())}
def result(s,kind,src,targets):
 if kind=='bidi':return s.search(src,next(iter(targets)))
 raw,parents,found=s.search(src,targets);paths={}
 for t in sorted(found):
  u=t;path=[]
  while u!=src:
   p,e=parents[u];path.append(e);u=p;assert len(path)<=s.n
  paths[t]=(raw[t],list(reversed(path)))
 return paths
counts={'paired_calls':0,'unread_price_perturbations':0,'observed_price_perturbations':0,'read_nodes':0}
for seed in range(200):
 rng=random.Random(seed);n=rng.randrange(3,30);f={'row_offsets':[0],'dest_ranks':[],'capacities':[1]*n};inc=[]
 for u in range(n):
  for v in range(n):
   if rng.random()<.1 or v==(u+1)%n:f['dest_ranks'].append(v);inc.append(rng.choice([0,0,1,7,2**40]))
  f['row_offsets'].append(len(inc))
 rc=SimpleNamespace(increments=inc,initial=lambda u:u%5)
 for kind,cls,old,new in [('forward',Forward,R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so',B/'forward.so'),('bidi',Bidirectional,R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so',B/'bidi.so')]:
  a=cls(f,rc,old);b=cls(f,rc,new)
  for step in range(12):
   src=rng.randrange(n);targets={rng.randrange(n)} if kind=='bidi' else set(rng.sample(range(n),rng.randrange(n+1)))
   prices={u:rng.randrange(8) for u in range(n)};weight=[0,1,17,2**63][step%4]
   a.prepare(prices,weight);b.prepare(prices,weight);trace(b);x=result(a,kind,src,targets);y=result(b,kind,src,targets);assert x==y,(seed,kind,step)
   d=deps(b);assert all(0<=u<n for u in d);counts['read_nodes']+=len(d);counts['paired_calls']+=1
   # Change only values not read in the complete old execution.
   changed={u:prices[u] if u in d else prices[u]+11 for u in range(n)}
   a.prepare(changed,weight);b.prepare(changed,weight);trace(b);xx=result(a,kind,src,targets);yy=result(b,kind,src,targets);assert xx==yy==x;assert deps(b)==d
   if len(d)<n:counts['unread_price_perturbations']+=1
   # An observed change is not certified; compute normally and compare kernels.
   if d:
    changed[min(d)]+=3;a.prepare(changed,weight);b.prepare(changed,weight);trace(b);assert result(a,kind,src,targets)==result(b,kind,src,targets);counts['observed_price_perturbations']+=1
  a.close();b.close()
receipt=json.loads((B/'receipt.json').read_text());bindings={**receipt['inputs'],**receipt['outputs']}
for p in [Path(__file__),R/'tools/build_price_read_trace_v1.py',R/'tools/soft_demand_workspace_bridge_v1.py',R/'tools/soft_demand_cpp_bridge_v1.py',R/'tools/bidirectional_rc_bridge_v1.py',R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so',R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so']:bindings[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in bindings.items())
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,random_graphs=200,counts=counts,scope='Standalone128 requested outputs and bidi work stats parity; sequential recomputation, including unread and observed price perturbations. No cache skips, native64, live transactions, bounded transcript or performance claim.'),indent=2)+'\n');print(counts)
