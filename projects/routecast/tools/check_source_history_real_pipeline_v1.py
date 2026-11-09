"""First declared case full off/on pipeline qualification, no quality evaluation."""
import sys,json,subprocess,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from run_external_source_history_feedback_v1 import predict
from source_binding_v2 import closure
from pre_route_endpoints import sha
E=R/'experiments';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';D=E/'source_history_real_pipeline_contract_v1_2026-10-20';P=E/'source_native_history_prior_v1_2026-10-20/prior.json'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);c=read(A/'protocol.json')['cases'][0];assert c['case']=='w160/episode_01';bindings=closure([Path(__file__),R/'tools/run_external_source_history_feedback_v1.py',R/'tools/verify_external_source_history_feedback_events_v1.py']);bindings[str(P)]=sha(P);contract=E/'source_history_lifecycle_contract_v1_2026-10-20/verification.json';assert all(sha(k)==h for k,h in read(contract)['bindings'].items());bindings[str(contract)]=sha(contract);(D/'protocol.json').write_text(json.dumps(dict(case=c,initializer='native_retained',policy='Full two rounds all NETs, first declared case only for new pipeline qualification; zero source prior must reproduce frozen full baseline, source prior ON retains identical initial paths/budgets and full event/timing audits. No forecast metrics or sample quality inference.',bindings=bindings),indent=2)+'\n');rows=[]
 for enabled,arm in [(False,'off'),(True,'on')]:
  out=D/arm;start=time.perf_counter();predict(c['endpoint'],out,c['node_base_proof'],c['criticality_directory'],str(Path(c['warm'])/'native_retained'),'all',timing_policy='warm_timing_round_updated',source_history_prior=str(P) if enabled else None);subprocess.run([sys.executable,str(R/'tools/verify_external_source_history_feedback_events_v1.py'),str(out),c['case'],str(out/'complete_event_audit.json')],cwd=R,check=True)
  baseline=A/c['case']/'native_retained/warm_timing_round_updated';assert read(out/'initial.json')==read(baseline/'initial.json')
  if not enabled:
   for name in ['round0.json','round1.json','sketch.json']:assert read(out/name)==read(baseline/name),name
  rows.append(dict(arm=arm,seconds=time.perf_counter()-start,complete_audit=True,initial_frame_unchanged=True,zero_full_state_reproduced=not enabled));print('ARM_QUALIFIED',arm,flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='FULL_FIRST_CASE_SOURCE_HISTORY_OFF_PARITY_ON_EVENT_PIPELINE_PASS',rows=rows,bindings=bindings,scope='Full first-case pipeline correctness, no all3 prediction quality or native utility claim.'),indent=2)+'\n')
if __name__=='__main__':main()
