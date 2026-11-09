"""Exhaustive small-DAG owner release and budget-envelope oracle."""
import sys,json,random,copy,time
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from budget_owner_screen_v1 import screen
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/budget_owner_screen_contract_v1_2026-10-07';out.mkdir();sources=closure([Path(__file__)]);(out/'protocol.json').write_text(json.dumps(dict(sources=sources,seed=20261007,trials=300,scope='Exhaustive small DAG necessary-owner/envelope oracle, no arbitrary cyclic/native claim.'))+'\n');rng=random.Random(20261007);baseline_fail=0;successes=0
for trial in range(300):
 n=6;arcs=[(u,v,rng.randrange(6)) for u in range(n) for v in range(u+1,n) if rng.random()<.45];offset=[0];dest=[];inc=[]
 for u in range(n):
  for a,v,d in arcs:
   if a==u:dest.append(v);inc.append(d)
  offset.append(len(dest))
 f=dict(row_offsets=offset,dest_ranks=dest,capacities=[rng.randrange(1,3) for _ in range(n)])
 class RC:
  increments=inc
  def initial(self,u):return initial
 initial=rng.randrange(4);q=dict(net_id=99,source=0,sink=5);forbidden={u for u in range(n) if rng.random()<.1};owners={net:{u for u in range(n) if rng.random()<.4} for net in (99,101,303,707)};budget=rng.randrange(16);before=copy.deepcopy((f,owners));result=screen(f,RC(),q,forbidden,owners,budget)
 def paths(extra=None,unrestricted=False):
  other=Counter(u for net,own in owners.items() if net not in (99,extra) for u in own);allowed=lambda u:u not in forbidden and (unrestricted or f['capacities'][u]>other[u]);options=[]
  def visit(u,d,used):
   if d>budget or not allowed(u):return
   if u==5:options.append(set(used));return
   for s in range(offset[u],offset[u+1]):visit(dest[s],d+inc[s],used+[dest[s]])
  visit(0,initial,[0]);return options
 envelope=set().union(*paths(unrestricted=True)) if paths(unrestricted=True) else set();assert set(result['envelope_nodes'])==envelope
 if not paths():
  baseline_fail+=1
  for net in (101,303,707):
   if paths(net):assert net in result['candidates'];successes+=1
 assert (f,owners)==before
try:screen(f,RC(),q,forbidden,owners,budget,deadline=time.perf_counter()-1)
except TimeoutError:pass
else:raise AssertionError('expired screen allowed')
assert all(sha(k)==v for k,v in sources.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),trials=300,baseline_failed_cases=baseline_fail,single_owner_successes_all_retained=successes,exact_dag_budget_envelope_pass=True,caller_unchanged=True,expired_request_rejected=True),indent=2)+'\n');print('PASS',baseline_fail,successes)
