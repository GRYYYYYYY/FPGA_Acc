"""All-nine matched quality effects, including mixed metric changes."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_prepared_map_replication_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 review=read(D/'terminal_review_v1.json');workflow=read(D/'workflow.json');oldworkflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json');oldfrozen=read(E/'wbuart_native_evaluation_v1_2026-10-20/declared_frozen_timing_ablation_v1/workflow.json');rows=[];bindings={str(p):sha(p) for p in [Path(__file__),D/'terminal_review_v1.json',D/'workflow.json']}
 for c in workflow['comparisons']:
  old=oldworkflow if c['timing_policy']=='warm_timing_round_updated' else oldfrozen;prior=next(r for r in old['comparisons'] if r['case']==c['case']);a,b=read(c['comparison']),read(prior['comparison']);deltas={}
  for method in ['native_retained_on','raw_min_on']:
   deltas[method]={}
   for scope in ['resource','spatial']:
    x,y=a['metrics'][method][scope],b['metrics'][method][scope];deltas[method][scope]={'rho_delta':x['spearman']-y['spearman'],'top_k_hit_delta':x['top_k_hits']-y['top_k_hits']}
  rows.append({'case':c['case'],'timing_policy':c['timing_policy'],'original_gate':b['pass_case_gate'],'candidate_gate':a['pass_case_gate'],'deltas':deltas});bindings[c['comparison']]=sha(c['comparison']);bindings[prior['comparison']]=sha(prior['comparison'])
 assert len(rows)==18
 p=D/'matched_quality_effect_v1.json';assert not p.exists();p.write_text(json.dumps({'status':'ALL18_FIXED_CASE_POLICY_MATCHED_QUALITY_EFFECTS_REPORTED','rows':rows,'bindings':bindings,'scope':'Posthoc paired effect of frozen MAP weighted queue priority change on exposed family. Report all cases and metrics, not replacement gates or unseen evidence.'},indent=2)+'\n');print('ALL18_FIXED_CASE_POLICY_MATCHED_QUALITY_EFFECTS_REPORTED')
if __name__=='__main__':main()
