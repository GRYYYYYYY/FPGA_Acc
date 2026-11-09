"""Parity with the actual frozen Python search block, including >64-bit weighted costs."""
import sys,ast,json,random,heapq
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from soft_demand_cpp_bridge_v1 import Search
source=R/'tools/trial_soft_demand_feedback_v1.py';tree=ast.parse(source.read_text());outer=next(x for x in tree.body if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='round_index');transaction=next(x for x in outer.body if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='net');stop=next(i for i,x in enumerate(transaction.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='oldepoch' for t in x.targets));code=compile(ast.fix_missing_locations(ast.Module(body=transaction.body[:stop],type_ignores=[])),str(source),'exec');binary=R/'experiments/soft_demand_cpp_build_v1_2026-10-07/search.so';cases=0
class RC:
 def __init__(self,inc,initial):self.increments=inc;self.value=initial
 def initial(self,node):return self.value
for seed in range(200):
 rng=random.Random(seed);n=rng.randrange(2,14);rows=[0];dest=[];inc=[]
 for u in range(n):
  for v in range(n):
   if u!=v and rng.random()<.24:dest.append(v);inc.append(rng.randrange(7))
  rows.append(len(dest))
 f=dict(row_offsets=rows,dest_ranks=dest,capacities=[int(rng.random()>.2) for _ in range(n)]);f['capacities'][0]=1;rc=RC(inc,rng.randrange(4));sinks=set(rng.sample(range(n),rng.randrange(1,n+1)));qs=[dict(connection_id=i,source=0,sink=s) for i,s in enumerate(sorted(sinks))];price=Counter({i:rng.randrange(6) for i in range(n)});weight=(1<<50) if seed%10==0 else rng.randrange(8)
 if seed%10==0:price=Counter({i:c*(1<<50) for i,c in price.items()})
 scope=dict(groups={0:qs},net=0,rc=rc,f=f,heapq=heapq,prices=price,weight=weight);exec(code,scope);cpp=Search(f,rc,binary);cpp.prepare(price,weight);raw,parents,reached=cpp.search(0,sinks);assert reached==scope['settled'].intersection(sinks);assert {i for i,x in enumerate(cpp.settled) if x}==scope['settled']
 for node,val in scope['raw'].items():assert raw[node]==val
 for node,parent in scope['parents'].items():assert parents[node]==parent
 cases+=1
# Bounds must reject unsafe input before accepting any output.
try:cpp.prepare(Counter({0:(1<<64)-1}), (1<<64)-1)
except AssertionError:pass
else:raise AssertionError('120-bit bound guard did not reject')
out=R/'experiments/soft_demand_cpp_contract_v1_2026-10-07';out.mkdir();bindings={**closure([Path(__file__)]),str(source):sha(source),str(binary):sha(binary),str(R/'tools/soft_demand_cpp/tree_v1.cpp'):sha(R/'tools/soft_demand_cpp/tree_v1.cpp')};(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,actual_python_block_random_cases=cases,weighted_costs_above_uint64_covered=True,unsafe_bound_rejected=True,scope='Deterministic queue/node tie, zero-cost cycles, disabled destinations, multi-sink/unreachable/initial cost and wide weighted costs against actual frozen Python block; not native or whole workflow benefit.'),indent=2)+'\n');print('PASS C++ search parity',cases,flush=True)
