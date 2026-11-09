"""Signed work attribution by first/later native iteration; descriptive, not causal."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 review=R/'experiments/mmc_preferred_NET_native_utility_review_v1_2026-10-19/research_decision_v1.json';decision=json.loads(review.read_text());assert decision['status']=='ALL3_FROZEN_NATIVE_COMPONENT_COMPARISONS_COMPLETE';parity=R/'experiments/mmc_preferred_hint_runtime_parity_v1_2026-10-19/independent_verification_v1.json';assert json.loads(parity.read_text())['status']=='ALL9_FULL_ARTIFACT_CONNECTION_TRACE_NATIVE_WORK_AND_EMPTY_SCOPE_COVERAGE_PASS';bindings={str(p):sha(p) for p in [review,parity,Path(__file__).resolve()]};rows=[];keys=['NET_operations','connection_operations','heap_pushes','heap_pops']
 for case in ['episode_01','episode_02','episode_03']:
  paths={'preferred':R/f'experiments/mmc_preferred_NET_owner_replay_v1_2026-10-19/{case}_preferred.json',**{arm:R/f'experiments/mmc_first_iteration_hint_trace_replay_v1_2026-10-19/{case}_{arm}.json' for arm in ['zero','forecast']}};arms={}
  for arm,p in paths.items():
   doc=json.loads(p.read_text());assert doc['status']=='pass' and doc['exact_native_work_counters_equal'];stats=doc['iteration_stats'];assert stats and stats[0]['iteration']==1
   arms[arm]={'iterations':len(stats),'first':{k:stats[0][k] for k in keys},'later':{k:sum(s[k] for s in stats[1:]) for k in keys},'total':{k:sum(s[k] for s in stats) for k in keys}};bindings[str(p)]=sha(p)
  deltas={}
  for baseline in ['zero','forecast']:
   deltas[baseline]={phase:{k:arms['preferred'][phase][k]-arms[baseline][phase][k] for k in keys} for phase in ['first','later','total']}
   assert all(deltas[baseline]['first'][k]+deltas[baseline]['later'][k]==deltas[baseline]['total'][k] for k in keys)
  rows.append({'case':case,'arms':arms,'preferred_minus_baseline':deltas})
 O=R/'experiments/mmc_preferred_NET_work_phase_diagnosis_v1_2026-10-19';O.mkdir(exist_ok=False);(O/'review.json').write_text(json.dumps({'status':'ALL3_SIGNED_FIRST_LATER_WORK_ACCOUNTING_COMPLETE','cases':rows,'bindings':bindings,'scope':'Exact measured counter decomposition only. Historical baseline traces admitted through exact disabled/empty reference parity. Not causal attribution, policy retuning, primary gate replacement or full workflow gain.'},indent=2)+'\n')
 print('PREFERRED_SIGNED_PHASE_DIAGNOSIS_COMPLETE')
if __name__=='__main__':main()
