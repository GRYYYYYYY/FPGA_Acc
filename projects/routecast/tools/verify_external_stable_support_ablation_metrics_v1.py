"""Independent average-rank/hit arithmetic for the frozen stable-support diagnostic."""
import sys,json
from pathlib import Path
from collections import Counter
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from verify_external_zero_feedback_warm_metrics_v1 import correlation
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_temporal_owner_turnover_v1_2026-10-19';P=R/'experiments/prospective_external_family_temporal_prior_errors_v1_2026-10-19';T=R/'experiments/prospective_external_family_temporal_prior_utilization_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 receipt=read(D/'verification.json');assert all(sha(p)==h for p,h in receipt['bindings'].items());cases=read(D/'protocol.json')['cases'];rows=[]
 for case,result in zip(cases,receipt['rows']):
  assert case['case']==result['case'];s=read(case['original_comparison_spec']);folder=Path(s['domain_proof']).parent;resources=[json.loads(x) for x in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');proof=read(s['domain_proof']);table=[json.loads(x) for x in (P/case['case']/'resources.jsonl').read_text().splitlines()];a={r['id']:F(1) if r['old'] and r['current'] else F(*r['score']) for r in table};b={r['id']:F(r['truth']) for r in table};vectors=[]
  for scores in [a,b]:
   totals=Counter()
   for r in resources:
    for k in r['bins']:totals[tuple(k)]+=scores[r['id']]
   vectors.append(dict(resource=scores,spatial={tuple(r['key']):totals[tuple(r['key'])]/r['capacity'] for r in bins}))
  checks={};controls=read(T/case['case']/'comparison.json')['metrics']
  for scope,k in [('resource',proof['resource_k']),('spatial',proof['spatial_k'])]:
   a,b=[v[scope] for v in vectors];ids=sorted(a);rho=correlation([a[n] for n in ids],[b[n] for n in ids]);hits=len(set(sorted(ids,key=lambda n:(-a[n],n))[:k])&set(sorted(ids,key=lambda n:(-b[n],n))[:k]));m=result['ablation_metrics'][scope];assert abs(rho-m['spearman'])<1e-12 and hits==m['top_k_hits'];checks[scope]=(rho,hits);rows.append(dict(case=case['case'],scope=scope,spearman=rho,top_k_hits=hits))
  passes=[]
  for name in ['previous_native','raw_min_on']:
   nonreg=[];strict=[]
   for scope,(rho,hits) in checks.items():
    c=controls[name][scope];nonreg.extend([rho>=c['spearman']-1e-12,hits>=c['top_k_hits']]);strict.extend([rho>c['spearman']+1e-12,hits>c['top_k_hits']])
   passed=all(nonreg) and any(strict);assert passed==result['ablation_checks'][name]['pass_primary_gate'];passes.append(passed)
  assert all(passes)==result['ablation_case_gate']
 with (D/'independent_metrics_verification_v1.json').open('x') as f:json.dump(dict(status='ALL6_STABLE_SUPPORT_ABLATION_METRIC_VECTORS_AND_GATES_VERIFIED',rows=rows,bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)}),f,indent=2)
 print('ALL6_STABLE_SUPPORT_METRICS_AND_GATES_VERIFIED')
if __name__=='__main__':main()
