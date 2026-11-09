"""Random sequential envelope parity with Fraction reference and atomic errors."""
import json,random
from pathlib import Path
from fractions import Fraction as F
from exact_incremental_timing_dag import ExactTimingDAG
from exact_connection_budget import connection_cap
from integer_connection_budget import IntegerConnectionBudget
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];rng=random.Random(9071);checks=0
for _ in range(200):
 nodes=list(range(15));budgets={str(c):F(rng.randrange(10),17) for c in range(5)}
 edges=[(u,v,F(rng.randrange(-2,8),13),str(rng.randrange(5)) if rng.random()<.85 else None) for v in nodes for u in range(v) if rng.random()<.2]
 dag=ExactTimingDAG(nodes,edges,[12,13,14],budgets);updates=[{str(rng.randrange(5)):F(rng.randrange(12),19)} for _ in range(20)];targets=[F(rng.randrange(100),23) for _ in updates]
 engine=IntegerConnectionBudget(dag,extra_values=targets+[x for update in updates for x in update.values()])
 for changes,target in zip(updates,targets):
  dag.update(changes,commit=True);engine.update(changes)
  for cid in budgets:assert engine.cap(cid,target)==connection_cap(dag,cid,target);checks+=1
 before=dict(engine.budgets)
 for changes in ({'0':F(1),'missing':F(1)},{'0':-1},{'0':True},{'0':1.0},{'0':F(1,999983)},{'0':F(1),0:F(2)}):
  try:engine.update(changes)
  except ValueError:pass
  else:raise AssertionError('invalid update accepted')
  assert engine.budgets==before
# No fixed-width overflow: target and encoded budgets well above128bits.
big=2**180;dag=ExactTimingDAG([0,1,2],[(0,1,F(1),'x'),(1,2,F(1),'x')],[2],{'x':F(big)});engine=IntegerConnectionBudget(dag)
assert engine.cap('x',F(2*big+2))==connection_cap(dag,'x',F(2*big+2))
out=ROOT/'experiments/integer_connection_budget_contract_2026-10-07';out.mkdir(exist_ok=True);r=dict(sources={str(p):sha(p) for p in (Path(__file__),ROOT/'tools/integer_connection_budget.py',ROOT/'tools/exact_connection_budget.py',ROOT/'tools/exact_incremental_timing_dag.py')},graphs=200,sequential_cap_comparisons=checks,invalid_atomic_update_checks=1200,above128bit_case=True,status='PASS',scope='Exact Fraction parity including repeated uses, negative offsets/zero clamps, updates and declared-lattice rejection. No quantization or fixed width. Synthetic contract only; real candidate/runtime pending.')
(out/'verification.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
