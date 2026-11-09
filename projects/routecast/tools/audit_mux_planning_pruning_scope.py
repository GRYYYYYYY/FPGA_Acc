"""Classify bounded planning rejection scope without asserting infeasibility."""
import json
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'experiments/mux_heuristic_budget_cohort_2026-10-07'
out=ROOT/'experiments/mux_planning_pruning_scope_2026-10-07';out.mkdir(exist_ok=True)
p=json.loads((base/'protocol.json').read_text());rows=[];bindings={}
for case in p['cases']:
 w,i=case['width'],case['index'];seed=ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json';a=json.loads(seed.read_text());ep=json.loads(Path(case['target']).read_text());qs={q['connection_id']:q for q in ep['connections']};initial=set(a['expanded_connection_ids']);retained=set(qs)-initial
 row=dict(width=w,index=i,initial_status=a['status'],initial_planning_cpd_ns=a['model_floor_cpd_ns'],target_cpd_ns=a['target_cpd_ns'],initial_added_nets=a['added_nets'],initial_retained_connections=len(retained),conditional_rejections=[],newly_expanded_seed_retained_connections=[])
 file=base/f'w{w}_m{i}/result.json'
 if file.exists():
  d=json.loads(file.read_text());proof=file.parent/'floor_verification.json';assert json.loads(proof.read_text())['result_sha256']==sha(file)
  bindings[str(file)]=sha(file);bindings[str(proof)]=sha(proof)
  for s in d['allocations']:
   expanded=set(s['expanded']);new=expanded&retained
   if new:row['newly_expanded_seed_retained_connections'].append(dict(allocation=s['index'],connection_ids=sorted(new)))
   if s['valid']:continue
   cpdbad=F(s['floor_cpd_ns'])>F(a['target_cpd_ns']);caps=[cid for cid in expanded if F(s['floor_ns'][str(cid)])>1]
   row['conditional_rejections'].append(dict(allocation=s['index'],planning_cpd_ns=s['floor_cpd_ns'],planning_cpd_exceeds_target=cpdbad,expanded_cap_exceeded=caps,retained_outside_expansion=len(set(qs)-expanded),newly_expanded_from_seed_retained=sorted(new),support_may_also_fail=True,scope='Bounded allocation rejection, not global routability infeasibility. Floor proof authenticates implementation, not universal retained-delay minima.'))
 for f in (seed,Path(case['target'])):bindings[str(f)]=sha(f)
 rows.append(row)
summary=dict(cases=len(rows),initial_skips=sum(r['initial_status']!='CRITICAL_RELEASE_VECTOR_CONSTRUCTED' for r in rows),conditional_rejections=sum(len(r['conditional_rejections']) for r in rows),cpd_rejections=sum(s['planning_cpd_exceeds_target'] for r in rows for s in r['conditional_rejections']),cap_rejections=sum(bool(s['expanded_cap_exceeded']) for r in rows for s in r['conditional_rejections']),allocations_expanding_seed_retained=sum(len(r['newly_expanded_seed_retained_connections']) for r in rows))
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),protocol_sha256=sha(base/'protocol.json'),bindings=bindings,summary=summary,rows=rows,scope='Structural audit of initial max4 critical-release planning and all archived conditional allocations. No shortest minima recomputed; no global infeasibility/native timing/benefit claim. Policy unchanged.'),indent=2)+'\n');print(summary)
