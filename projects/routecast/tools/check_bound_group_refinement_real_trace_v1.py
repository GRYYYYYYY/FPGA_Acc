"""Three-case known-pair serialized-loop/auditor regression; not full forecast study."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from run_bound_group_refinement_case_v1 import execute
from source_binding_v2 import closure
from pre_route_endpoints import sha
E=R/'experiments';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';S=E/'prospective_external_family_blocker_root_pair_schedule_v2_2026-10-20';D=E/'bound_group_refinement_real_trace_contract_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def main():
 proof=read(S/'independent_verification_v1.json');assert proof['status']=='ALL3_ALL_RR_ROOT_BLOCKER_SCHEDULES_INDEPENDENT_XML_OWNER_RECONSTRUCTION_PASS';D.mkdir(exist_ok=False);cases=read(A/'protocol.json')['cases'];bindings=closure([Path(__file__),R/'tools/run_bound_group_refinement_case_v1.py',R/'tools/verify_sequential_group_refinement_v1.py']);bindings[str(S/'independent_verification_v1.json')]=sha(S/'independent_verification_v1.json');schedule_dir=D/'schedules'
 for c in cases:
  full=read(S/c['case']/'schedule.json');single=[q for q in full if q['members']==[3279,3280]];assert len(single)==1;p=schedule_dir/c['case']/'schedule.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(single)+'\n');bindings[str(p)]=sha(p)
 protocol=dict(require_archived_zero_state_match=False,cases=cases,bindings=bindings,policy='Known-pair end-to-end serialized event regression only. Full all-RR schedules remain fixed and unexecuted.10000 perquery labels; current source history/criticality; no shared external state.');(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for c in cases:
  execute(c,protocol,D,schedule_dir)
  for arm in ['off','on']:
   audit=read(D/c['case']/arm/'complete_event_audit.json');assert audit['groups']==1 and audit['complete_periodic_actual_state_digest_and_final_frame_rebuild_pass'];rows.append(dict(case=c['case'],arm=arm,counts=audit['counts']))
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_OFF_ON_REAL_SERIALIZED_GROUP_LOOP_AND_INDEPENDENT_AUDITOR_CONTRACT_PASS',rows=rows,bindings=bindings,scope='One existing known pair per case validates new event pipeline, no full forecast or performance conclusion.'),indent=2)+'\n');print('ALL3_OFF_ON_REAL_SERIALIZED_GROUP_LOOP_AND_INDEPENDENT_AUDITOR_CONTRACT_PASS',flush=True)
if __name__=='__main__':main()
