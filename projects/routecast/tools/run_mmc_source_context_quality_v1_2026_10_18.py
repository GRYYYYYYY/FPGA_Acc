"""Registered both-input primary, all3 source arms, unchanged original cold gate."""
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';root=E/'mmc_source_context_ablation_v1_2026-10-18';audit=root/'independent_audits/verification.json';v=json.loads(audit.read_text());assert v['all9_full_frames_and_source_context_event_replays_pass'] and all(sha(k)==h for k,h in v['bindings'].items());out=E/'mmc_source_context_quality_v1_2026-10-18';out.mkdir(exist_ok=False);arms=['source_history_only','source_post_STA_only','source_history_and_post_STA'];rows=[];bindings={**closure([Path(__file__)]),str(audit):sha(audit)}
 for case in ['case_01','case_02','case_03']:
  old=E/f'mmc_multiplacement_quality_v1_2026-10-18/{case}/protocol.json';p=json.loads(old.read_text());p['bindings'].update(closure([Path(__file__)]));p['bindings'][str(old)]=sha(old);p['bindings'][str(audit)]=sha(audit);p['source_context_audit']=str(audit);p['source_context_arms']=arms
  for arm in arms:p['predictions'][arm]=str(root/case/arm/'sketch.json')
  p['primary_candidate']='source_history_and_post_STA';p['evidence_scope']='Registered both-input primary; other source input arms are fixed ablations, no posthoc arm selection. All3 exposed layouts, original cold labels/domains/tie/K rules and raw_min_on/previous_native controls unchanged. Source postSTA prior is not target STA. No native utility, accepted complete workflow gain, heldout or hardware claim.';folder=out/case;folder.mkdir();(folder/'protocol.json').write_text(json.dumps(p,indent=2))
  for script in ['evaluate_source_context_quality_case_v1_2026_10_18.py','verify_source_context_quality_case_v1_2026_10_18.py']:
   with (folder/f'{script}.log').open('x') as log:code=subprocess.call([sys.executable,str(R/'tools'/script),str(folder)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
   print('SOURCE_CONTEXT_QUALITY',case,script,code,flush=True);assert code==0
  r=json.loads((folder/'comparison.json').read_text());a=json.loads((folder/'verification.json').read_text());assert a['status']=='pass' and a['histogram_rank_topk_mae_checks']==16 and a['truth_tie_interval_checks']==16 and a['primary_gate_pass']==r['primary_gate_pass'];assert all(sha(k)==h for k,h in a['bindings'].items());bindings[str(folder/'comparison.json')]=sha(folder/'comparison.json');bindings[str(folder/'verification.json')]=sha(folder/'verification.json');rows.append(dict(case=case,primary_gate_pass=r['primary_gate_pass'],primary_checks=r['primary_checks']))
 (out/'results.json').write_text(json.dumps(dict(bindings=bindings,cases=rows,primary_candidate='source_history_and_post_STA',all3_original_cold_primary_gate_pass=all(r['primary_gate_pass'] for r in rows)),indent=2))
if __name__=='__main__':main()
