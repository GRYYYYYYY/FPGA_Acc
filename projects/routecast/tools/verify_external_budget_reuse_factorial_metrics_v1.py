"""Independent fixed factorial metric reconstruction and original gate replay."""
import json
from pathlib import Path
from fractions import Fraction
from collections import Counter
from pre_route_endpoints import sha
from verify_external_zero_feedback_warm_metrics_v1 import correlation
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_budget_reuse_factorial_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def accepted(a,b):
 good=[];strict=[]
 for scope in ['resource','spatial']:
  x,y=a[scope],b[scope];rx,ry=x['spearman'],y['spearman'];defined=rx is not None and ry is not None;good.extend([defined and rx>=ry-1e-12,x['top_k_hits']>=y['top_k_hits']]);strict.extend([defined and rx>ry+1e-12,x['top_k_hits']>y['top_k_hits']])
 return all(good) and any(strict)
def main():
 summary=read(D/'quality_summary.json');p=read(D/'protocol.json');assert summary['status']=='ALL12_FROZEN_BUDGET_REUSE_FACTORIAL_ARMS_EVALUATED';assert len(summary['rows'])==12
 for receipt in [summary,p]:assert all(sha(q)==h for q,h in receipt['bindings'].items())
 rows={(r['case'],r['initializer'],r['head']):r for r in summary['rows']};assert len(rows)==12;bindings={str(q):sha(q) for q in [Path(__file__).resolve(),R/'tools/verify_external_zero_feedback_warm_metrics_v1.py',D/'protocol.json',D/'quality_summary.json']};checks=0;all_rows=[]
 for spec in p['cases']:
  original=read(spec['original_spec']);dp=Path(original['domain_proof']);meta=read(dp);assert all(sha(q)==h for q,h in meta['bindings'].items());resources=[json.loads(s) for s in (dp.parent/'resources.jsonl').read_text().splitlines()];binrows=read(dp.parent/'spatial_bins.json');capacities={tuple(x['key']):x['capacity'] for x in binrows};physical=read(original['label_physical_audit']);cache={}
  def scores(ledger):
   concrete={};space=Counter()
   for r in resources:
    n=r['id'];v=ledger.get(n,0);concrete[n]=Fraction(v,r['capacity'])
    for k in r['bins']:space[tuple(k)]+=v
   return dict(resource=concrete,spatial={k:Fraction(space[k],c) for k,c in capacities.items()})
  truth=scores({int(n):v for n,v in physical['node_occupancy'].items()})
  def metric(frame,clip):
   key=(frame,clip)
   if key in cache:return cache[key]
   ledger={int(n):v for n,v in read(frame)['ledger'].items()}
   if clip:ledger={r['id']:min(ledger.get(r['id'],0),r['capacity']) for r in resources}
   pred=scores(ledger);result={}
   for scope,k in [('resource',meta['resource_k']),('spatial',meta['spatial_k'])]:
    ids=sorted(truth[scope]);pv=sorted(ids,key=lambda n:(-pred[scope][n],n))[:k];tv=sorted(ids,key=lambda n:(-truth[scope][n],n))[:k];result[scope]=dict(spearman=correlation([pred[scope][n] for n in ids],[truth[scope][n] for n in ids]),top_k_hits=len(set(pv)&set(tv)),k=k,universe_size=len(ids),prediction_top_k=[list(x) if isinstance(x,tuple) else x for x in pv],truth_top_k=[list(x) if isinstance(x,tuple) else x for x in tv])
   cache[key]=result;return result
  old=metric(spec['original_global_frame'],False)
  for arm in spec['arms']:
   row=rows[spec['case'],arm['initializer'],arm['head']];sp=read(row['comparison_spec']);c=read(row['comparison']);assert sp['predictions']['native_retained_on']==dict(frame=arm['frame'],proof=arm['proof']);assert all(sp[k]==original[k] for k in ['case','endpoint','domain_proof','domain_independent_proof','source_frame','source_proof','label_proof','label_physical_audit']);assert sp['predictions']['raw_min_on']==original['predictions']['raw_min_on'];methods={'previous_native':metric(sp['source_frame'],False),'raw_min_on':metric(sp['predictions']['raw_min_on']['frame'],False),'native_retained_on':metric(arm['frame'],arm['head']=='capacity_bounded_utilization')}
   for name,m in methods.items():
    for scope in ['resource','spatial']:
     actual=c['metrics'][name][scope];expected=m[scope]
     for k in ['top_k_hits','k','universe_size','prediction_top_k','truth_top_k']:assert actual[k]==expected[k]
     a,b=actual['spearman'],expected['spearman'];assert a is None and b is None or a is not None and b is not None and abs(a-b)<1e-12;checks+=1
   passed=all(accepted(methods['native_retained_on'],methods[name]) for name in ['previous_native','raw_min_on']);assert passed==c['pass_case_gate']==row['original_registered_case_gate'];assert accepted(methods['native_retained_on'],old)==row['vs_original_global_candidate']['pass_primary_gate'];all_rows.append(dict(case=spec['case'],initializer=arm['initializer'],head=arm['head'],registered_gate=passed))
 assert checks==72;assert summary['all9_availability_pass'] is False and len(summary['unavailable_cases'])==6;assert all(sha(q)==h for q,h in bindings.items());(D/'independent_metrics_verification_v1.json').write_text(json.dumps(dict(status='ALL72_BUDGET_REUSE_FACTORIAL_METRIC_VECTORS_AND_ORIGINAL_GATES_VERIFIED',metric_checks=checks,rows=all_rows,bindings=bindings,scope='Fixed2x2 all3 development factorial. Original controls/labels/domains/K/four gates unchanged. No per-case winner selection, strict-unseen/full9/native utility/time or hardware promotion.'),indent=2)+'\n');print('PASS',checks,'passed arms',sum(r['registered_gate'] for r in all_rows))
if __name__=='__main__':main()
