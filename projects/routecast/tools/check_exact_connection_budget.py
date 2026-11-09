"""Enumerate all small DAG paths independently to validate analytic caps."""
import json,random
from pathlib import Path
from fractions import Fraction as F
from exact_incremental_timing_dag import ExactTimingDAG
from exact_connection_budget import connection_cap
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];rng=random.Random(7107);checks=0;repeated=0
for _ in range(200):
 nodes=list(range(8));edges=[(u,v,F(rng.randrange(10),13),str(rng.randrange(3))) for v in nodes for u in range(v) if rng.random()<.35];budgets={str(k):F(rng.randrange(9),17) for k in range(4)};sinks=[6,7];dag=ExactTimingDAG(nodes,edges,sinks,budgets)
 for cid in budgets:
  target=F(rng.randrange(50),19);terms={n:[(0,F(0))] for n in nodes}
  for n in nodes:
   for u,v,offset,c in edges:
    if v==n:terms[n].extend((k+int(c==cid),base+offset+(budgets[c] if c!=cid else 0)) for k,base in terms[u])
  paths=[term for n in sinks for term in terms[n]];feasible=all(base<=target for k,base in paths);expected=min(((target-base)/k for k,base in paths if k),default=None) if feasible else None
  before=dict(dag.budgets),dict(dag.arrivals);result=connection_cap(dag,cid,target);assert result['feasible']==feasible and result['cap_ns']==expected
  if feasible:
   cap=expected if expected is not None else F(10**6)
   assert dag.update({cid:cap})<=target
   if expected is not None:assert dag.update({cid:cap+F(1,10**9)})>target
   repeated+=result['maximum_repetitions']>1
  else:assert dag.update({cid:F(0)})>target
  assert (dag.budgets,dag.arrivals)==before;checks+=1
out=ROOT/'experiments/exact_connection_budget_contract_2026-10-07';out.mkdir(exist_ok=True)
r=dict(sources={str(p):sha(p) for p in (Path(__file__),ROOT/'tools/exact_connection_budget.py',ROOT/'tools/exact_incremental_timing_dag.py')},graphs=200,enumerated_cap_comparisons=checks,feasible_repeated_connection_cases=repeated,status='PASS',scope='Exact all-path enumeration and boundary/infeasibility checks, state unchanged. Caps conditional on all other delays fixed; simultaneous cap application not guaranteed. Model only, no native STA or netgain claim.')
(out/'verification.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
