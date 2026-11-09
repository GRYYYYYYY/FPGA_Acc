"""Heuristic envelope relaxation never relaxes floors or expanded caps."""
import json
from pathlib import Path
from fractions import Fraction as F
from heuristic_connection_budget_allocation import allocate_budget
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
count=0
def evaluate(b):
 global count
 count+=1
 return sum(b.values())
floor={0:F(1,5),1:F(1,5)};initial={0:F(4,5),1:F(4,5)}
value,valid,budget,policy,alpha=allocate_budget(floor,{0,1},initial,F(1),{0:{7}},True,evaluate)
assert valid and value==F(2,5) and budget==initial and policy=='HEURISTIC_PRESERVE_WITH_CONDITIONAL_FLOORS' and alpha is None
assert evaluate(budget)>1 # Explicitly NOT a worst-budget timing certificate.
actual={0:F(2,5),1:F(2,5)};assert evaluate(actual)<=1 and all(actual[c]<=budget[c] for c in actual)
actual_bad={0:F(7,10),1:F(7,10)};assert all(actual_bad[c]<=budget[c] for c in actual_bad) and evaluate(actual_bad)>1 # Candidate postcheck must reject.
assert not allocate_budget(floor,{0,1},initial,F(1),{0:{7}},False,evaluate)[1]
assert not allocate_budget({0:F(11,10)},{0},{0:F(11,10)},F(2),{0:{7}},True,evaluate)[1]
r=allocate_budget(floor,{0,1},{0:F(6,5),1:F(4,5)},F(1),{0:{7}},True,evaluate)
assert r[3]=='UNIFORM_INTERPOLATION' and r[4]==F(3,8) and evaluate(r[2])==1
r=allocate_budget(floor,{0,1},{0:F(2,5),1:F(2,5)},F(1),{},True,evaluate)
assert r[3]=='INITIAL_NET_SLACK_VECTOR' and r[4] is None
out=ROOT/'experiments/mux_heuristic_budget_contract_2026-10-07';out.mkdir()
(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),allocator_sha256=sha(ROOT/'tools/heuristic_connection_budget_allocation.py'),scope='Synthetic envelope failure allowed only as routing heuristic; explicit under-budget actual vector can pass OR fail target, proving need for postcheck. Unsupported/cap rejection and exact uniform fallback preserved; initial certified vector unchanged. No physical/native performance claim.'),indent=2)+'\n');print('heuristic allocator contract passed')
