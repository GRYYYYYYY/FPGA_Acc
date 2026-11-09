"""Independent histogram/joint-score reconstruction of frozen tie diagnostics."""
import json
from pathlib import Path
from collections import Counter
from fractions import Fraction
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_score_label_tie_diagnosis_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=read(D/'verification.json');protocol=read(D/'protocol.json');assert proof['status']=='ALL36_FIXED_SCORE_LABEL_TIE_DIAGNOSTICS_PREPARED';assert proof['original_quality_gates_changed'] is False
 for p in [proof,protocol]:assert all(sha(k)==h for k,h in p['bindings'].items())
 observed={(r['case'],r['method'],r['scope']):r for r in proof['rows']};assert len(observed)==len(proof['rows'])==36;bindings={str(p):sha(p) for p in [Path(__file__).resolve(),D/'verification.json',D/'protocol.json']};checks=0;labels=[]
 def boundary(values,k):
  histogram=Counter(values);above=0
  for value,count in sorted(histogram.items(),reverse=True):
   if above+count>=k:return value,dict(boundary=str(value),above=above,tied=count,selected_from_tie=k-above)
   above+=count
  raise AssertionError('k')
 def weight(value,cut,profile):return Fraction(1) if value>cut else Fraction(profile['selected_from_tie'],profile['tied']) if value==cut else Fraction(0)
 for spec in protocol['cases']:
  dp=Path(spec['domain_proof']);meta=read(dp);ind=read(spec['domain_independent_proof']);assert ind['status']=='ALL3_EXPAT_RESOURCE_IDENTITIES_INCLUSIVE_BINS_CAPACITIES_AND_K_EXACT'
  for p in [meta,ind]:assert all(sha(k)==h for k,h in p['bindings'].items())
  resources=[json.loads(s) for s in (dp.parent/'resources.jsonl').read_text().splitlines()];binrows=read(dp.parent/'spatial_bins.json');cap={tuple(r['key']):r['capacity'] for r in binrows};native={int(n):v for n,v in read(spec['label_physical_audit'])['node_occupancy'].items()};assert all(0<=native.get(r['id'],0)<=r['capacity'] for r in resources);all_ledgers={'truth':native}
  for arm in spec['arms']:all_ledgers[arm['name']]={int(n):v for n,v in read(arm['frame'])['ledger'].items()}
  vectors={}
  for name,ledger in all_ledgers.items():
   node={};space=Counter()
   for r in resources:
    node[r['id']]=Fraction(ledger.get(r['id'],0),r['capacity'])
    for key in r['bins']:space[tuple(key)]+=ledger.get(r['id'],0)
   vectors[name]={'resource':node,'spatial':{key:Fraction(space[key],capacity) for key,capacity in cap.items()}}
  labels.append(dict(case=spec['case'],resource_capacities=sorted({r['capacity'] for r in resources}),label_score_values=sorted(str(v) for v in set(vectors['truth']['resource'].values())),occupied_resources=sum(v>0 for v in vectors['truth']['resource'].values()),resource_k=meta['resource_k']))
  for arm in spec['arms']:
   for scope,k in [('resource',meta['resource_k']),('spatial',meta['spatial_k'])]:
    prediction=vectors[arm['name']][scope];truth=vectors['truth'][scope];ids=sorted(truth);a,pa=boundary(prediction.values(),k);b,pb=boundary(truth.values(),k);joint=Counter((prediction[n],truth[n]) for n in ids);expected=sum((count*weight(x,a,pa)*weight(y,b,pb) for (x,y),count in joint.items()),Fraction(0));fixed_a=set(sorted(ids,key=lambda n:(-prediction[n],n))[:k]);fixed_b=set(sorted(ids,key=lambda n:(-truth[n],n))[:k]);hits=len(fixed_a&fixed_b);r=observed[spec['case'],arm['name'],scope];assert r['prediction']==pa and r['truth']==pb and r['fixed_ID_hits']==hits;assert Fraction(r['fixed_ID_precision'])==Fraction(hits,k) and Fraction(r['independent_uniform_tie_expected_hits'])==expected and Fraction(r['independent_uniform_tie_expected_precision'])==expected/k;assert r['truth_distinct_scores']==len(set(truth.values())) and r['prediction_distinct_scores']==len(set(prediction.values()));assert r['truth_positive']==sum(v>0 for v in truth.values());assert r['predicted_over_capacity_resources']==sum(all_ledgers[arm['name']].get(x['id'],0)>x['capacity'] for x in resources);checks+=1
 assert checks==36;assert all(sha(p)==h for p,h in bindings.items());(D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL36_SCORE_LABEL_PROFILES_FIXED_TOPK_AND_INDEPENDENT_TIE_EXPECTATIONS_RECONSTRUCTED',checks=checks,labels=labels,bindings=bindings,scope='Secondary diagnostic only. Independent tie choices are not a replacement accuracy definition; no original gate/label changes or predictor promotion.'),indent=2)+'\n');print('PASS',checks,json.dumps(labels))
if __name__=='__main__':main()
