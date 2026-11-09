"""Independently verify all216 vectors,72 gates and original2round comparisons."""
import json,hashlib
from pathlib import Path
from verify_wbuart_primary_metrics_v1 import scores,rho
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_fixed_horizon_trial_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'comparison.json';v=read(p);assert all(sha(n)==h for n,h in v['bindings'].items());rows=[];count=0
 for c in v['rows']:
  domain=read(c['domain_proof']);folder=Path(c['domain_proof']).parent;resources=[json.loads(s) for s in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');target=scores(resources,bins,{int(n):x for n,x in read(c['label'])['node_occupancy'].items()});computed={}
  for method,frame in c['frames'].items():
   pred=scores(resources,bins,{int(n):x for n,x in read(frame)['ledger'].items()});computed[method]={};count+=1
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
    r=rho(pred[scope],target[scope]);a=sorted(pred[scope],key=lambda n:(-pred[scope][n],n))[:k];b=sorted(target[scope],key=lambda n:(-target[scope][n],n))[:k];hits=len(set(a)&set(b));got=c['metrics'][method][scope];assert got['k']==k and got['universe_size']==len(pred[scope]) and got['top_k_hits']==hits;assert (r is None and got['spearman'] is None) or r is not None and abs(got['spearman']-r)<1e-12;assert got['prediction_top_k']==[list(x) if isinstance(x,tuple) else x for x in a] and got['truth_top_k']==[list(x) if isinstance(x,tuple) else x for x in b];computed[method][scope]=(r,hits)
  checks={}
  for control in ['previous_native','raw_min_on']:
   nonreg=[];strict=[]
   for scope in ['resource','spatial']:
    a,h=computed['native_retained_on'][scope];b,j=computed[control][scope];defined=a is not None and b is not None;nonreg.extend([defined and a>=b-1e-12,h>=j]);strict.extend([defined and a>b+1e-12,h>j])
   checks[control]=all(nonreg) and any(strict);assert checks[control]==c['checks'][control]['pass_primary_gate']
  passed=all(checks.values());assert passed==c['diagnostic_same_rule_pass']
  if c['horizon']==2:
   old=E/'wbuart_native_evaluation_v1_2026-10-20';workflow=read(old/('workflow.json' if c['timing_policy']=='warm_timing_round_updated' else 'declared_frozen_timing_ablation_v1/workflow.json'));prior=read(next(x['comparison'] for x in workflow['comparisons'] if x['case']==c['case']));assert passed==prior['pass_case_gate']
   for method in c['metrics']:
    for scope in ['resource','spatial']:
     a,b=c['metrics'][method][scope],prior['metrics'][method][scope];assert abs(a['spearman']-b['spearman'])<1e-12 and a['top_k_hits']==b['top_k_hits']
  rows.append({'case':c['case'],'timing_policy':c['timing_policy'],'horizon':c['horizon'],'diagnostic_same_rule_pass':passed})
 assert count==216 and len(rows)==72
 summary={policy:{str(h):sum(r['diagnostic_same_rule_pass'] for r in rows if r['timing_policy']==policy and r['horizon']==h) for h in [2,4,8,16]} for policy in ['warm_timing_frozen','warm_timing_round_updated']}
 (D/'independent_metrics_verification_v1.json').write_text(json.dumps({'status':'ALL216_VECTORS72_GATES_AND_ORIGINAL2ROUND_METRICS_INDEPENDENTLY_VERIFIED','rows':rows,'metric_vectors':216,'pass_counts':summary,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'All fixed horizons reported; original2round primary unchanged. No best-horizon promotion, unseen or native/full paid gain.'},indent=2)+'\n');print(summary)
if __name__=='__main__':main()
