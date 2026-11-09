"""Retrospective evaluator equivalence only; no native/search acceptance claim."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from exact_incremental_timing_dag import ExactTimingDAG
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'experiments/mux_net_slack_online_loop_2026-10-06'
out=ROOT/'experiments/mux_incremental_online_allocation_replay_2026-10-06'
out.mkdir()
rows=[]
for w in (8,16,32):
 for i in range(4):
  file=base/f'w{w}_m{i}/result.json'
  if not file.exists():continue
  d=json.loads(file.read_text());meta=json.loads((ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json').read_text());tg=json.loads((ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json').read_text());mapping=json.loads((ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json').read_text());initial=json.loads((ROOT/f'experiments/mux_net_slack_budgets_2026-10-06/w{w}_m{i}.json').read_text());target=F(meta['target_cpd_ns']);start=time.perf_counter();dag=ExactTimingDAG.from_native_metadata(tg,mapping,meta,initial['initial_budgets_ns']);evaluations=0
  for spec in d['allocations']:
   floor={k:F(v) for k,v in spec['floor_ns'].items()};expanded=set(map(str,spec['expanded']));dag.update(floor,commit=True);assert dag.cpd==F(spec['floor_cpd_ns']);evaluations+=1
   if not spec['valid']:
    assert not spec['budgets_ns'] and spec['budget_cpd_ns'] is None
    continue
   budget=dict(floor);low=F(0);high=F(1)
   for _ in range(24):
    mid=(low+high)/2;trial={k:v+mid*(1-v) if k in expanded else v for k,v in floor.items()}
    if dag.update(trial)<=target:budget=trial;low=mid
    else:high=mid
    evaluations+=1
   assert low==F(spec['interpolation'])
   policy='UNIFORM_INTERPOLATION'
   if not spec['restrictions']:
    budget={k:F(v) for k,v in initial['budgets_ns'].items()};policy='INITIAL_NET_SLACK_VECTOR'
   else:
    preserved={k:max(F(initial['budgets_ns'][k]),v) for k,v in floor.items()}
    if all(preserved[k]<=1 for k in expanded) and dag.update(preserved)<=target:
     budget=preserved;policy='PRESERVE_INITIAL_WITH_CONDITIONAL_FLOORS'
   assert policy==spec['budget_policy'] and budget=={k:F(v) for k,v in spec['budgets_ns'].items()}
   assert dag.update(budget)==F(spec['budget_cpd_ns']);assert dag.budgets==floor
  rows.append(dict(width=w,index=i,result_sha256=sha(file),allocations=len(d['allocations']),evaluations=evaluations,replay_seconds=time.perf_counter()-start));print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),evaluator_sha256=sha(ROOT/'tools/exact_incremental_timing_dag.py'),baseline_audit_sha256=sha(base/'audit_summary.json'),rows=rows,scope='Retrospective archived conditional floor vectors only. Exact 24-step interpolation/preserved policy/budget/CPD parity, transaction restoration. Invalid support floors and routing/search outcomes require independent audits and prospective rerun. No cold oracle in prospective producer.'),indent=2)+'\n')
