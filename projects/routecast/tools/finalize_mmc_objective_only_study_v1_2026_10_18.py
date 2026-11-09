"""Close one frozen objective-only admission study; never promote automatically."""
import pathlib,json,sys,time,os
R=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';root=E/'mmc_objective_only_all_NET_v1_2026-10-18';quality=E/'mmc_objective_only_quality_v1_2026-10-18';target=quality/'results.json';live=json.loads((quality/'live_process.json').read_text());s=pathlib.Path('/proc/self/stat').read_text().split(') ',1)[1].split();control=root/'finalizer_live_process.json'
 with control.open('x') as f:json.dump({'pid':os.getpid(),'startticks':s[19]},f)
 while not target.exists():
  try:st=pathlib.Path(f'/proc/{live["pid"]}/stat').read_text().split(') ',1)[1].split();running=st[19]==live['startticks'] and st[0]!='Z'
  except FileNotFoundError:running=False
  if not running and not target.exists():raise RuntimeError('Quality owner stopped without terminal result; no retry')
  time.sleep(15)
 bindings=closure([pathlib.Path(__file__)])
 def load(p):
  p=pathlib.Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
 q=load(target);a=load(root/'independent_audits/verification.json');assert a['all3_objective_only_frames_and_all331800_events_pass'];assert q['status']=='all3_fixed_four_control_quality_evaluations_independently_verified';assert all(sha(k)==h for obj in [q,a] for k,h in obj['bindings'].items());models=load(root/'results.json');rows=[]
 for case in ['case_01','case_02','case_03']:
  final=load(root/case/'sketch.json');baseline=load(E/f'mmc_all_NET_feedback_v1_2026-10-18/{case}/sketch.json');assert final['budget_policy']=='NATIVE_ENDPOINT_ANCHORED_PROXY_V2' and final['original_monotone_overflow_gate_claimed'] is False;assert all(x['answer']['delay']<=x['budget_integer'] for x in final['records']);actual={x['connection_id']:x for x in final['records']};old={x['connection_id']:x for x in baseline['records']};assert actual.keys()==old.keys();events=load(root/f'independent_audits/{case}_events.json');assert events['events']==110600 and events['complete_objective_only_admission_and_unchanged_rejected_epoch_pass'];v=load(quality/case/'verification.json');assert v['status']=='pass' and v['histogram_rank_topk_mae_checks']==16
  rows.append(dict(case=case,overflow_units=final['overflow_units'],original_monotone_overflow_units=baseline['overflow_units'],original_hard_budget_violations=0,positive_overflow_commits=events['positive_overflow_commits'],positive_overflow_units=events['positive_overflow_units'],path_changed_CIDs_vs_original_allNET=sum(actual[c]['answer']['physical_edge_ids']!=old[c]['answer']['physical_edge_ids'] for c in actual),quality_primary_gate_pass=v['primary_gate_pass']))
 passed=all(x['quality_primary_gate_pass'] for x in rows);assert passed==q['all3_primary_gate_pass'];component=models['shared_graph_setup_seconds']+sum(x['compiled_workspace_setup_seconds']+x['result']['total_paid_resident_seconds'] for x in models['cases']);decision=dict(status='fixed_objective_only_study_closed_quality_pass_native_utility_pending' if passed else 'fixed_objective_only_study_closed_quality_failed_no_native_promotion',bindings=bindings,cases=rows,all3_primary_quality_gate_pass=passed,independently_verified_metric_vectors=48,model_component_seconds=component,timing_scope='Disjoint model graph/workspace/predictor clocks only, not complete acquisition/conversion/audit/quality/native route workflow.',original_monotone_overflow_gate_claimed=False,original_hard_budget_policy_preserved=True,original_zero_counter_gate_claimed=False,strict_unseen_admitted=False,accepted_gain=False,new_native_utility_jobs=0,next_action='Keep all fixed outcomes; no selection of rounds, thresholds or budgets. Only independently qualified quality and full native STA/QoR/complete-cost evidence could justify later promotion.')
 (root/'research_decision_v1.json').write_text(json.dumps(decision,indent=2)+'\n');cp=E/'mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json';c=json.loads(cp.read_text());c['mmc_objective_only_all_NET_v1'].update(status=decision['status'],decision=str(root/'research_decision_v1.json'),decision_sha256=sha(root/'research_decision_v1.json'),primary_gate_pass=passed,independent_audits_pending=False,accepted_gain=False);tmp=cp.with_suffix('.tmp');tmp.write_text(json.dumps(c,indent=2)+'\n');os.replace(tmp,cp);print('OBJECTIVE_ONLY_STUDY_CLOSED',decision['status'],flush=True)
if __name__=='__main__':main()
