"""Independent exact vectors, tie-rank metrics and original gates for all3 cases."""
import json,sys
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from verify_external_zero_feedback_warm_metrics_v1 import correlation
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_primary_budget_repair_bounded_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 summary=read(D/'quality_summary.json');assert len(summary['rows'])==3 and all(r['process_exit']==0 for r in summary['rows']);assert all(sha(p)==h for p,h in summary['bindings'].items());bindings=dict(summary['bindings']);bindings[str(D/'quality_summary.json')]=sha(D/'quality_summary.json');bindings[str(Path(__file__).resolve())]=sha(__file__);rows=[];decisions=[]
 for case in summary['rows']:
  folder=D/case['case'];spec=read(folder/'comparison_spec.json');result=read(folder/'comparison.json');bindings.update(result['bindings']);domain=Path(spec['domain_proof']).parent;resources=[json.loads(x) for x in (domain/'resources.jsonl').read_text().splitlines()];bins=read(domain/'spatial_bins.json');proof=read(spec['domain_proof']);ledgers={'truth':{int(n):v for n,v in read(spec['label_physical_audit'])['node_occupancy'].items()}}
  for name,path in [('previous_native',spec['source_frame']),*[(k,v['frame']) for k,v in spec['predictions'].items()]]:ledgers[name]={int(n):v for n,v in read(path)['ledger'].items()}
  vectors={}
  for name,ledger in ledgers.items():
   if name=='native_retained_on':ledger={r['id']:min(ledger.get(r['id'],0),r['capacity']) for r in resources}
   totals=Counter()
   for r in resources:
    for key in r['bins']:totals[tuple(key)]+=ledger.get(r['id'],0)
   vectors[name]=dict(resource={r['id']:F(ledger.get(r['id'],0),r['capacity']) for r in resources},spatial={tuple(b['key']):F(totals[tuple(b['key'])],b['capacity']) for b in bins})
  values={}
  for method in ['native_retained_on','previous_native','raw_min_on']:
   values[method]={}
   for scope,k in [('resource',proof['resource_k']),('spatial',proof['spatial_k'])]:
    a,b=vectors[method][scope],vectors['truth'][scope];ids=sorted(b);rho=correlation([a[n] for n in ids],[b[n] for n in ids]);p=sorted(ids,key=lambda n:(-a[n],n))[:k];t=sorted(ids,key=lambda n:(-b[n],n))[:k];hits=len(set(p)&set(t));observed=result['metrics'][method][scope];assert observed['k']==k and observed['universe_size']==len(ids) and observed['top_k_hits']==hits and abs(observed['spearman']-rho)<1e-12;assert observed['prediction_top_k']==[list(n) if isinstance(n,tuple) else n for n in p];values[method][scope]=(rho,hits);rows.append(dict(case=case['case'],method=method,scope=scope,spearman=rho,top_k_hits=hits))
  outcomes=[]
  for control in ['previous_native','raw_min_on']:
   checks=[];strict=[]
   for scope in ['resource','spatial']:
    a,h=values['native_retained_on'][scope];b,j=values[control][scope];checks.extend([a>=b-1e-12,h>=j]);strict.extend([a>b+1e-12,h>j])
   passed=all(checks) and any(strict);assert passed==result['checks'][control]['pass_primary_gate'];outcomes.append(passed)
  assert all(outcomes)==result['pass_case_gate']==case['original_case_gate'];decisions.append(dict(case=case['case'],pass_case_gate=all(outcomes)))
 assert all(sha(p)==h for p,h in bindings.items())
 with (D/'independent_metrics_verification_v1.json').open('x') as f:json.dump(dict(status='ALL18_BOUNDED_PRIMARY_BUDGET_REPAIR_AND_CONTROL_METRIC_VECTORS_AND_ORIGINAL_GATES_VERIFIED',rows=rows,decisions=decisions,bindings=bindings,scope='Same labels/domains/K/controls/gates. No strict unseen/full9/native utility/time/hardware admission.'),f,indent=2)
 print('ALL18_BOUNDED_PRIMARY_BUDGET_REPAIR_METRICS_AND_GATES_VERIFIED')
if __name__=='__main__':main()
