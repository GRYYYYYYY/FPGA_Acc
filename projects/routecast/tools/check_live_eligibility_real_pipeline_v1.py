"""Complete first declared case control/live pipeline qualification, no scores."""
import sys,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from run_external_live_eligibility_feedback_v1 import predict
from source_binding_v2 import closure
from pre_route_endpoints import sha
E=R/'experiments';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';D=E/'live_eligibility_real_pipeline_contract_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);c=read(A/'protocol.json')['cases'][0];assert c['case']=='w160/episode_01';bindings=closure([Path(__file__),R/'tools/run_external_live_eligibility_feedback_v1.py',R/'tools/verify_external_live_eligibility_feedback_events_v1.py'])
 for p in [E/'live_overuse_eligibility_contract_v1_2026-10-20/verification.json',E/'live_overuse_eligibility_design_v1_2026-10-20/protocol.json']:
  q=read(p);assert all(sha(k)==h for k,h in q['bindings'].items());bindings[str(p)]=sha(p)
 (D/'protocol.json').write_text(json.dumps(dict(case=c,bindings=bindings,policy='First declared case native_retained complete2rounds, source history OFF. Control all-NET final/round states reproduce baseline. Live policy traverses all NET decisions with skip entries and independent current-owner predicate/epoch/ticket audits. No subset quality or speed inference.'),indent=2)+'\n');rows=[]
 for enabled,arm in [(False,'off'),(True,'on')]:
  out=D/arm;start=time.perf_counter();predict(c['endpoint'],out,c['node_base_proof'],c['criticality_directory'],str(Path(c['warm'])/'native_retained'),'live_overuse' if enabled else 'all',timing_policy='warm_timing_round_updated',source_history_prior=None);subprocess.run([sys.executable,str(R/'tools/verify_external_live_eligibility_feedback_events_v1.py'),str(out),c['case'],str(out/'complete_event_audit.json')],cwd=R,check=True);baseline=A/c['case']/'native_retained/warm_timing_round_updated';assert read(out/'initial.json')==read(baseline/'initial.json')
  if not enabled:
   for name in ['round0.json','round1.json','sketch.json']:assert read(out/name)==read(baseline/name),name
  audit=read(out/'complete_event_audit.json');assert audit['complete_live_eligibility_predicates_skip_state_and_ticket_replay_pass'];assert read(out/'source_initial_history.json')=={};rows.append(dict(arm=arm,events=audit['events'],skipped=audit['skipped_current_clean'],initial_frame_unchanged=True,zero_control_state_reproduced=not enabled,seconds=time.perf_counter()-start));print('ARM_QUALIFIED',arm,flush=True)
 assert all(sha(k)==h for k,h in bindings.items())
 for arm in ['off','on']:
  for name in ['complete_event_audit.json','initial.json','round0.json','round1.json','sketch.json']:
   p=D/arm/name;bindings[str(p)]=sha(p)
 (D/'verification.json').write_text(json.dumps(dict(status='FULL_FIRST_CASE_LIVE_ELIGIBILITY_OFF_PARITY_ON_EVENT_PIPELINE_PASS',rows=rows,bindings=bindings,scope='First-case full pipeline correctness only. No all3 quality, native timing-force equivalence or net time admission.'),indent=2)+'\n')
if __name__=='__main__':main()
