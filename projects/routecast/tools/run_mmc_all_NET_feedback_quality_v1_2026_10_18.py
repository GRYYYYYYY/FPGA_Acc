"""Original cold gate with all-NET candidate and local/owner supplemental arms."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';source=E/'mmc_all_NET_feedback_v1_2026-10-18';audit=source/'independent_audits/verification.json';v=json.loads(audit.read_text());assert v['all3_full_frames_and_all_NET_event_replays_pass'] and all(sha(k)==h for k,h in v['bindings'].items());out=E/'mmc_all_NET_feedback_quality_v1_2026-10-18';out.mkdir(exist_ok=False);rows=[];bindings={**closure([Path(__file__)]),str(audit):sha(audit)}
 for case in ['case_01','case_02','case_03']:
  old=E/f'mmc_multiplacement_quality_v1_2026-10-18/{case}/protocol.json';p=json.loads(old.read_text());p['bindings'].update(closure([Path(__file__)]));p['bindings'][str(old)]=sha(old);p['bindings'][str(audit)]=sha(audit);p['all_NET_audit']=str(audit);p['owner_frame_audit']=str(E/f'mmc_owner_expansion_feedback_v1_2026-10-18/independent_audits/{case}_frame.json');p['predictions']['owner_expansion_on']=str(E/f'mmc_owner_expansion_feedback_v1_2026-10-18/{case}/sketch.json');p['predictions']['all_NET_on']=str(source/case/'sketch.json');p['primary_candidate']='all_NET_on';p['evidence_scope']='Uniform all55300 NET scheduling per original2rounds; all3 exposed development cases. Original cold labels/full positive domains/tie rules/TopK/controls preserved. Local and owner-expanded supplemental arms. No heldout, native utility, accepted complete workflow timing or hardware claim.';folder=out/case;folder.mkdir();(folder/'protocol.json').write_text(json.dumps(p,indent=2))
  for script in ['evaluate_all_NET_feedback_quality_case_v1_2026_10_18.py','verify_all_NET_feedback_quality_case_v1_2026_10_18.py']:
   with (folder/f'{script}.log').open('x') as log:code=subprocess.call([sys.executable,str(R/'tools'/script),str(folder)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
   print('ALL_NET_QUALITY',case,script,code,flush=True);assert code==0
  result=json.loads((folder/'comparison.json').read_text());verification=json.loads((folder/'verification.json').read_text());assert verification['status']=='pass' and verification['histogram_rank_topk_mae_checks']==14 and verification['truth_tie_interval_checks']==14 and verification['primary_gate_pass']==result['primary_gate_pass'];assert all(sha(k)==h for k,h in verification['bindings'].items());bindings[str(folder/'comparison.json')]=sha(folder/'comparison.json');bindings[str(folder/'verification.json')]=sha(folder/'verification.json');rows.append(dict(case=case,primary_gate_pass=result['primary_gate_pass'],primary_checks=result['primary_checks']))
 with (out/'results.json').open('x') as f:json.dump(dict(bindings=bindings,cases=rows,all3_original_cold_primary_gate_pass=all(r['primary_gate_pass'] for r in rows)),f,indent=2)
if __name__=='__main__':main()
