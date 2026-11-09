"""All6 archived warm snapshots checked through independent XML audit adapter."""
import sys,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from independent_fraction_arc_context_v2 import load_context
from audit_fixed_nominal_round_timing_v1 import audit
from pre_route_endpoints import sha
E=R/'experiments';D=E/'prospective_external_family_fixed_nominal_independent_preflight_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);g=E/'prospective_external_family_width_frame_inputs_v1_2026-10-19/w160/source/rr_graph.xml';xml,ids,classes,switches,digest=load_context(g,sha(g));rows=[]
 for episode in ('episode_01','episode_02','episode_03'):
  case='w160/'+episode;ep=E/'prospective_external_family_width_frame_inputs_v1_2026-10-19'/case/'endpoints.json'
  for init in ('raw_min','native_retained'):
   old=E/'prospective_external_family_fixed_nominal_feedback_contract_v2_2026-10-19'/case/init/'criticalities.json';source=E/'prospective_external_family_corrected_native_epoch_v1_2026-10-19/warm'/case/init/'initial.json';records=json.loads(source.read_text())['records'];out=D/case/init;out.mkdir(parents=True);shutil.copyfile(source,out/'initial.json');(out/'timing_round0.json').write_text(json.dumps(dict(policy='warm_timing_frozen',round_index=0,source_state=str(out/'initial.json'),criticalities=json.loads(old.read_text())))+'\n');v=audit(out,0,'warm_timing_frozen',records,ep,xml,classes,switches);rows.append(dict(case=case,initializer=init,connections=len(v)));print(rows[-1],flush=True)
 (D/'verification.json').write_text(json.dumps(dict(status='ALL6_INDEPENDENT_XML_ROUND_TIMING_AUDIT_PASS',rows=rows),indent=2)+'\n')
if __name__=='__main__':main()
