"""Original cold gates with independently admitted owner-expanded predictions."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';source=E/'mmc_owner_expansion_feedback_v1_2026-10-18';audit=source/'independent_audits/verification.json';v=json.loads(audit.read_text());assert v['all3_full_frames_and_owner_expanded_event_replays_pass'];assert all(sha(p)==h for p,h in v['bindings'].items())
 out=E/'mmc_owner_expansion_quality_v1_2026-10-18';out.mkdir(exist_ok=False);rows=[];bindings={**closure([Path(__file__)]),str(audit):sha(audit)}
 for case in ['case_01','case_02','case_03']:
  old=E/f'mmc_multiplacement_quality_v1_2026-10-18/{case}/protocol.json';p=json.loads(old.read_text());p['bindings'].update(closure([Path(__file__)]));p['bindings'][str(old)]=sha(old);p['bindings'][str(audit)]=sha(audit);p['owner_expansion_audit']=str(audit);p['predictions']['owner_expansion_on']=str(source/case/'sketch.json');p['primary_candidate']='owner_expansion_on';p['evidence_scope']='All3 exposed development layouts; owner-expanded scheduling only. Exact original cold labels, full domains, tie and TopK rules, raw_min_on/previous_native primary controls. Original local native_retained_on remains supplemental. No heldout or native utility or complete workflow gain claim.';folder=out/case;folder.mkdir();(folder/'protocol.json').write_text(json.dumps(p,indent=2))
  for script in ['evaluate_owner_expansion_quality_case_v1_2026_10_18.py','verify_owner_expansion_quality_case_v1_2026_10_18.py']:
   with (folder/f'{script}.log').open('x') as log:code=subprocess.call([sys.executable,str(R/'tools'/script),str(folder)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
   print('QUALITY',case,script,code,flush=True);assert code==0
  r=json.loads((folder/'comparison.json').read_text());verified=json.loads((folder/'verification.json').read_text());assert verified['status']=='pass' and verified['primary_gate_pass']==r['primary_gate_pass'] and verified['histogram_rank_topk_mae_checks']==12;assert all(sha(k)==h for k,h in verified['bindings'].items());bindings[str(folder/'comparison.json')]=sha(folder/'comparison.json');bindings[str(folder/'verification.json')]=sha(folder/'verification.json');rows.append(dict(case=case,primary_gate_pass=r['primary_gate_pass'],primary_checks=r['primary_checks']))
 (out/'results.json').write_text(json.dumps(dict(bindings=bindings,cases=rows,all3_original_cold_primary_gate_pass=all(r['primary_gate_pass'] for r in rows)),indent=2))
if __name__=='__main__':main()
