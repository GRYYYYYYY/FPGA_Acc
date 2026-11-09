"""Independent full-domain tie ranks/topK and source/parent gates for every stage."""
import sys,json,hashlib
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from verify_external_zero_feedback_warm_metrics_v1 import correlation
E=R/'experiments';D=E/'wbuart_quality_stage_diagnosis_v1_2026-10-20';L=E/'prospective_external_family_live_eligibility_trial_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def improve(a,b):
 good=[];strict=[]
 for scope in ['resource','spatial']:
  x,h=a[scope];y,j=b[scope];good.extend([x>=y-1e-12,h>=j]);strict.extend([x>y+1e-12,h>j])
 return all(good) and any(strict)
def main():
 p=D/'verification.json';v=read(p);assert all(sha(k)==h for k,h in v['bindings'].items());cases=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons'];rows=[];stage_count=0
 for row in v['rows']:
  case=next(c for c in cases if c['case']==row['case']);spec=read(case['specification']);folder=Path(spec['domain_proof']).parent;domain=read(spec['domain_proof']);resources=[json.loads(s) for s in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');truth={int(n):x for n,x in read(spec['label_physical_audit'])['node_occupancy'].items()}
  def vector(ledger):
   sums=Counter()
   for resource in resources:
    for key in resource['bins']:sums[tuple(key)]+=ledger.get(resource['id'],0)
   return dict(resource={r['id']:F(ledger.get(r['id'],0),r['capacity']) for r in resources},spatial={tuple(r['key']):F(sums[tuple(r['key'])],r['capacity']) for r in bins})
  targets=vector(truth);values={}
  for stage in row['stages']:
   frame=read(stage['frame']);pred=vector({int(n):x for n,x in frame['ledger'].items()});current={}
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
    ids=sorted(targets[scope]);a=pred[scope];b=targets[scope];rho=correlation([a[n] for n in ids],[b[n] for n in ids]);hits=len(set(sorted(ids,key=lambda n:(-a[n],n))[:k])&set(sorted(ids,key=lambda n:(-b[n],n))[:k]));observed=stage['metrics'][scope];assert observed['k']==k and observed['universe_size']==len(ids) and observed['top_k_hits']==hits and abs(observed['spearman']-rho)<1e-12;current[scope]=(rho,hits)
   values[stage['stage']]=current;stage_count+=1
   if stage['gate_vs_source'] is not None:assert improve(current,values['source_native'])==stage['gate_vs_source']['pass_primary_gate']
   if stage['parent'] is not None:assert improve(current,values[stage['parent']])==stage['gate_vs_parent']['pass_primary_gate']
  rows.append(dict(case=row['case'],stages=len(values),all_rank_metrics_and_original_source_parent_gates_verified=True))
 assert stage_count==99 and all(sha(k)==h for k,h in v['bindings'].items());(D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL99_STAGE_METRICS_AND_ORIGINAL_FOUR_METRIC_TRANSITIONS_INDEPENDENT_PASS',stages=stage_count,rows=rows,bindings={str(p):sha(p),str(Path(__file__)):sha(__file__)},scope='Original fixed domains/labels/K; posthoc stage diagnosis only, no policy tuning, label changes or quality promotion.'),indent=2)+'\n');print('ALL99_STAGE_METRICS_AND_ORIGINAL_FOUR_METRIC_TRANSITIONS_INDEPENDENT_PASS')
if __name__=='__main__':main()
