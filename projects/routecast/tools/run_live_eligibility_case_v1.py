"""All four initializer/scheduling arms; source history OFF, no target labels."""
import sys,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from run_external_live_eligibility_feedback_v1 import predict
from pre_route_endpoints import sha
E=R/'experiments';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';D=E/'prospective_external_family_live_eligibility_trial_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 protocol=read(D/'protocol.json');assert all(sha(k)==h for k,h in protocol['bindings'].items());c=next(q for q in protocol['cases'] if q['case']==sys.argv[1]);rows=[]
 for enabled,arm in [(False,'off'),(True,'on')]:
  for init in ['raw_min','native_retained']:
   out=D/c['case']/init/arm;start=time.perf_counter();predict(c['endpoint'],out,c['node_base_proof'],c['criticality_directory'],str(Path(c['warm'])/init),'live_overuse' if enabled else 'all',timing_policy='warm_timing_round_updated',source_history_prior=None);subprocess.run([sys.executable,str(R/'tools/verify_external_live_eligibility_feedback_events_v1.py'),str(out),c['case'],str(out/'complete_event_audit.json')],cwd=R,check=True);audit=read(out/'complete_event_audit.json');assert audit['complete_live_eligibility_predicates_skip_state_and_ticket_replay_pass'];assert read(out/'source_initial_history.json')=={};baseline=A/c['case']/init/'warm_timing_round_updated';assert read(out/'initial.json')==read(baseline/'initial.json')
   if not enabled:
    for name in ['round0.json','round1.json','sketch.json']:assert read(out/name)==read(baseline/name),name
   rows.append(dict(initializer=init,arm=arm,initial_frame_unchanged=True,off_full_state_reproduced=not enabled,producer_and_audit_seconds=time.perf_counter()-start,skipped_current_clean=audit['skipped_current_clean']));print('ARM_AUDITED',c['case'],init,arm,flush=True)
 (D/c['case']/'arm_pipeline_verification.json').write_text(json.dumps(dict(rows=rows),indent=2)+'\n')
if __name__=='__main__':main()
