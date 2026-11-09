"""Synthetic fallback boundaries and archived all66 chosen-budget parity."""
import json
from pathlib import Path
from fractions import Fraction as F
from exact_incremental_timing_dag import ExactTimingDAG
from lazy_connection_budget_allocation import allocate_budget
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
# Explicit unsupported/cap rejection, initial/preserved shortcuts, full fallback.
floor={0:F(1,5),1:F(1,5)};snapshot=dict(floor)
evaluate=lambda b:sum(b.values())
r=allocate_budget(floor,{0,1},{0:F(2,5),1:F(2,5)},F(1),{},True,evaluate)
assert r[1] and r[3]=='INITIAL_NET_SLACK_VECTOR' and r[4] is None
r=allocate_budget({0:F(3,5),1:F(1,5)},{0,1},{0:F(2,5),1:F(1,5)},F(1),{1:{7}},True,evaluate)
assert r[2]=={0:F(3,5),1:F(1,5)} and r[4] is None
r=allocate_budget(floor,{0,1},{0:F(4,5),1:F(4,5)},F(1),{1:{7}},True,evaluate)
assert r[3]=='UNIFORM_INTERPOLATION' and r[4]==F(3,8) and sum(r[2].values())==1
assert not allocate_budget(floor,{0,1},floor,F(1),{},False,evaluate)[1]
assert not allocate_budget({0:F(11,10)},{0},{0:F(11,10)},F(3),{},True,evaluate)[1]
assert floor==snapshot
base=ROOT/'experiments/mux_owned_bound_cache_cohort_2026-10-06'
out=ROOT/'experiments/mux_lazy_budget_replay_2026-10-06';out.mkdir()
rows=[];shortcuts=0;total=0;calls=0
for w in (8,16,32):
 for i in range(4):
  file=base/f'w{w}_m{i}/result.json'
  if not file.exists():continue
  def read(path):return json.loads(path.read_text())
  data=read(file);meta=read(ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json');graph=read(ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json');mapping=read(ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json');seed=read(ROOT/f'experiments/mux_net_slack_budgets_2026-10-06/w{w}_m{i}.json');initial={int(k):F(v) for k,v in seed['budgets_ns'].items()};dag=ExactTimingDAG.from_native_metadata(graph,mapping,meta,seed['initial_budgets_ns'])
  case_calls=0
  def measured(b):
   global case_calls
   case_calls+=1
   return dag.update(b)
  for spec in data['allocations']:
   floor={int(k):F(v) for k,v in spec['floor_ns'].items()};dag.update(floor,commit=True)
   # Archived supported/invalid outcome is an input here, not independent solver proof.
   value,valid,budget,policy,alpha=allocate_budget(floor,set(spec['expanded']),initial,F(meta['target_cpd_ns']),spec['restrictions'],spec['valid'],measured)
   assert value==F(spec['floor_cpd_ns']) and valid==spec['valid']
   assert budget=={int(k):F(v) for k,v in spec['budgets_ns'].items()} and policy==spec['budget_policy']
   if valid:
    assert dag.update(budget)==F(spec['budget_cpd_ns'])
    if policy=='UNIFORM_INTERPOLATION':assert alpha==F(spec['interpolation'])
    else:assert alpha is None;shortcuts+=1
   assert dag.budgets=={str(k):v for k,v in floor.items()}
   total+=1
  calls+=case_calls;rows.append(dict(width=w,index=i,result_sha256=sha(file),allocations=len(data['allocations']),evaluate_calls=case_calls))
assert total==66 and shortcuts==47
(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),allocator_sha256=sha(ROOT/'tools/lazy_connection_budget_allocation.py'),baseline_audit_sha256=sha(base/'audit_summary.json'),rows=rows,allocations=total,shortcuts=shortcuts,evaluate_calls=calls,scope='Archived floors/restrictions/supported labels as inputs: chosen budgets/floorCPD/policy/exact fallback24grid unchanged for all66. Only unused alpha replaced by null in47validcases. Synthetic unsupported/cap/initial/preserved/fallback boundaries. Not prospective shortest-floor/branch/native acceptance proof.'),indent=2)+'\n');print(total,shortcuts,calls)
