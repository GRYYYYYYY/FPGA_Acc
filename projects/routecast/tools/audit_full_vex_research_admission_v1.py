"""Review full Vex functional eligibility without promoting local diagnostic passes."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_vex_research_admission_v1_2026-10-09';D.mkdir(exist_ok=True)
F=R/'experiments/full_ibus_fill_capture_preedge_trace_v1_2026-10-09/trace_audit.json';W=R/'experiments/full_ibus_write_history_preedge_trace_v1_2026-10-09/trace_audit.json';B=R/'experiments/full_ibus_bank_history_preedge_trace_v1_2026-10-09/trace_audit.json';S=R/'experiments/vexriscv_full_development_sdc_v1_2026-10-09/protocol.json';M=R/'experiments/ultraembedded_mmc_continuous_workflow_v4_2026-10-08/verification.json';a,w,b,s,m=[json.loads(p.read_text()) for p in [F,W,B,S,M]]
checked=0
for file,report in [(F,a),(W,w),(B,b)]:
 assert report['replay_fidelity'] and report['cycles']==512
 for name,expected in report['hashes'].items():
  path=file.parent/name;assert path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==expected,path;checked+=1
assert a['mismatches']==w['mismatches']==b['mismatches']==42370
assert len(w['write_address_comparisons'])==len(w['write_address_differences'])==152
assert m['all_cases_both_complete_arms_authenticated'] and not m['observed_single_trial_continuous_time_gain'] and m['seed_over_cold_ratio']>1
requirements=[
 {'requirement':'Original full functional baseline','status':'contradicted_for_this_replay','evidence':str(F.relative_to(R)),'observed_mismatches':42370,'passing_local_checks_do_not_override':True},
 {'requirement':'Original bank write address correspondence','status':'contradicted_for_this_replay','evidence':str(W.relative_to(R)),'write_address_differences':152},
 {'requirement':'Independent product timing','status':'not_established_by_development_sdc','evidence':str(S.relative_to(R)),'timing_origin':s['timing_origin'],'clock_ns':s['clock_ns'],'max_io_delay_ns':s['max_io_delay_ns']},
 {'requirement':'Unseen-family hotspot/routing validation','status':'not_established_by_vex_evidence','evidence':str(S.relative_to(R)),'recorded_family_status':s['unseen_family_status']},
 {'requirement':'Positive complete fixed-placement runtime benefit','status':'contradicted_for_archived_single_mmc_trial','evidence':str(M.relative_to(R)),'cold_seconds':m['cold_continuous_cohort_seconds'],'seed_seconds':m['seed_continuous_cohort_seconds'],'seed_over_cold':m['seed_over_cold_ratio'],'scope':m['scope']},
 {'requirement':'Affected updates, final route QoR, bounded hardware and physical card evidence','status':'not_audited_by_this_functional_review','evidence':'RESEARCH_PLAN.md','must_remain_in_full_objective':True}]
out={'admitted_full_vex_for_prediction':False,'research_goal_complete':False,'checked_current_trace_hashes':checked,'requirements':requirements,'next_work':{'functional':'Establish original valid/capture histories or an appropriately scoped proof; preserve failing replay, uninitialized state and counterexamples. Do not add arbitrary initialization or ignore failing comparisons.','scientific':'Use verified independent design families with frozen split and matched fixed-placement full timing/QoR protocol; test genuine estimator/feedback improvement. Existing development variants and local RTL checks cannot substitute for heldout or complete net benefit.'},'scope':'Current-state review of named evidence, not exhaustive certification of every repository result. JSON false admission is a scientific conclusion, not a tool failure or goal completion. No new simulation, route labels or performance outcome generated.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,W,B,S,M,R/'experiments/manifest.json',Path(__file__)]}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'admitted_full_vex_for_prediction':False,'checked_trace_hashes':checked,'mismatches':42370,'native_write_address_differences':152,'mmc_complete_runtime_ratio':m['seed_over_cold_ratio']},indent=2))
