"""Authoritative negative intervention ledger; distinguish protocols and controls."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E=R/'experiments';bindings={str(Path(__file__).resolve()):sha(Path(__file__).resolve())};rows=[]
 def load(path):
  d=json.loads(path.read_text());bindings[str(path)]=sha(path);return d
 def add(name,path,change,cases,controls,limits):
  assert len(cases)==3 and all(x is False for x in cases)
  rows.append(dict(intervention=name,decision=str(path.relative_to(R)),isolated_policy_or_registered_primary=change,case_primary_gates=cases,registered_controls=controls,interpretation_limit=limits))
 for name,change in [('mmc_owner_expansion_feedback_v1_2026-10-18','Endpoint closure union current overused resource owners, each original round'),('mmc_all_NET_feedback_v1_2026-10-18','All55300 NETs in each of the original two rounds')]:
  p=E/name/'research_decision_v1.json';d=load(p);add(name,p,change,[x['primary_gate_pass'] for x in d['cases']],['raw_min_on','previous_native'],'These fixed two-round scope policies failed; not proof that every global solver or scheduling policy fails.')
 p=E/'mmc_source_context_ablation_v1_2026-10-18/research_decision_v1.json';d=load(p);primary=d['registered_primary'];add('source_context_primary',p,primary,[x['arms'][primary]['pass_original_case_gate'] for x in d['cases']],['raw_min_on','previous_native'],'Source H and dense post-STA prior under unchanged factor1/local routing; not target STA or native price equivalence. The case02 post-STA-only secondary pass cannot replace registered primary.');assert d['ablation_original_cohort_gates']=={'source_history_only':False,'source_post_STA_only':False,'source_history_and_post_STA':False}
 p=E/'mmc_restart_present_schedule_v1_2026-10-18/research_decision_v1.json';d=load(p);add('restart_present_only',p,'Present schedule [0,1/2], all other original model mechanics unchanged',[x['primary_gate_pass'] for x in d['cases']],['raw_min_on','previous_native'],'Isolates present schedule only; does not reconstruct native retained restart initial history, timing, lookahead or search.')
 p=E/'mmc_fresh_timing_quality_v1_2026-10-18/cohort_research_decision_v1.json';d=load(p);add('target_initialized_criticality_only',p,'Refreshed target initial criticalities, unchanged endpoint-local two-round model',[x['primary_gate_pass'] for x in d['rows']],['native_retained_on','raw_min_on','previous_native'],'This historical experiment has one additional control; do not silently treat protocols as identical. Rank changes alone do not explain full cold rerouting.')
 pending=E/'mmc_native_first_iteration_v1_2026-10-18/physical_and_budget_verification_v1.json';physical=load(pending);assert all(not x['all_original_V2_budgets_pass'] for x in physical['cases']);partial=[]
 for case in ['case_01','case_02','case_03']:
  p=E/f'mmc_native_first_iteration_quality_v1_2026-10-18/{case}/verification.json'
  if p.exists():
   d=load(p);assert d['status']=='pass';partial.append(dict(case=case,quality_gate_pass=d['primary_gate_pass'],independent_vectors=d['histogram_rank_topk_mae_checks']))
 result=dict(status='closed_interventions_reconciled_native_first_iteration_quality_pending_unless_all3_reported',bindings=bindings,closed_interventions=rows,source_secondary_cohort_gates={'source_history_only':False,'source_post_STA_only':False,'source_history_and_post_STA':False},native_first_iteration=dict(original_V2_budget_violations=[x['budget_violations'] for x in physical['cases']],observed_independent_quality=partial,scope='Separate acquired diagnostic; not budget-admitted candidate, native FULL, promotion or complete-flow gain.'),research_constraints=['Do not repeat target initial criticality capture as a new hypothesis.','Do not select secondary arms/cases or tune coefficient/rounds/thresholds on these exposed labels.','Preserve original domains, K, ties, budgets, guards, failed comparisons and acquisition/checking costs.','No single negative ablation establishes a universal cause or impossibility theorem.','Strict unseen families, varied native failures, accepted matched complete-flow gain and physical hardware evidence remain unproven.'],next_action='Finish the fixed first-iteration diagnostic on all3 cases, then choose a distinct pre-route-available mechanism only from validated source/control-flow evidence. No automatic iteration sweep or native utility promotion.')
 out=E/'mmc_controlled_intervention_synthesis_v1_2026-10-18';out.mkdir();(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('FIVE_CLOSED_PRIMARY_INTERVENTIONS_RECONCILED',len(rows),'PREFIX_VERIFIED_CASES',len(partial))
if __name__=='__main__':main()
