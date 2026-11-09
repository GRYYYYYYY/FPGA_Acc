"""Same two-control four-metric gate; score-only projection, not route acceptance."""
import json
from pathlib import Path
from fractions import Fraction as Q
from pre_route_endpoints import sha
from external_forecast_metrics_v1 import vectors,metrics,gate
from audit_prince_forecast_metrics_v1 import check
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_capacity_projection_quality_v1_2026-10-20'
def encode(x):return json.loads(json.dumps(x,default=lambda v:dict(numerator=v.numerator,denominator=v.denominator)))
def main():
 D.mkdir(exist_ok=False);root=E/'prince_capacity_projection_v1_2026-10-20';vp=root/'verification.json';v=json.loads(vp.read_text());rawp=E/'prince_live_ready_quality_v1_2026-10-20/verification.json';unprojected={x['case']:x for x in json.loads(rawp.read_text())['rows']};bindings={str(q):sha(q) for q in [vp,rawp,Path(__file__)]};rows=[];checked=0
 for row in v['rows']:
  case=row['case']
  if row['status']!='SCORES_READY':rows.append(dict(case=case,status=row['status'],pass_both_controls=False));continue
  proof=Path(row['verification']);assert sha(proof)==row['sha256'];p=json.loads(proof.read_text());assert all(sha(f)==h for f,h in p['bindings'].items());forecast={r['id']:r for r in map(json.loads,Path(p['score_file']).open())};spec=E/'prince_feedback_quality_v1_2026-10-20'/case/'specification.json';s=json.loads(spec.read_text());dp=Path(s['domain_proof']);meta=json.loads(dp.read_text());rp=dp.parent/'resources.jsonl';bp=dp.parent/'spatial_bins.json';resources=list(map(json.loads,rp.open()));bins=json.loads(bp.read_text());assert set(forecast)=={r['id'] for r in resources};ledger={n:r['forecast_count'] for n,r in forecast.items()};label=Path(s['label_physical_audit']);truth={int(k):v for k,v in json.loads(label.read_text())['node_occupancy'].items()}
  for n,r in forecast.items():assert 0<=ledger[n]<=r['capacity'] and abs(ledger[n]-truth.get(n,0))<=abs(r['native_count']-truth.get(n,0))
  result=metrics(vectors(resources,bins,ledger,meta['graph_nodes']),vectors(resources,bins,truth,meta['graph_nodes'],truth=True),meta['resource_k'],meta['spatial_k']);coded=encode(result);adj={tuple(b['key']):[] for b in bins}
  for r in resources:
   for key in r['bins']:adj[tuple(key)].append(r['id'])
  def normalize(values):return dict(resource={r['id']:Q(values.get(r['id'],0),r['capacity']) for r in resources},spatial={tuple(b['key']):Q(sum(values.get(n,0) for n in adj[tuple(b['key'])]),b['capacity']) for b in bins})
  a,b=normalize(ledger),normalize(truth)
  for scope,k in [('resource',meta['resource_k']),('spatial',meta['spatial_k'])]:check(a[scope],b[scope],k,coded[scope]);checked+=1
  cp=spec.parent/'comparison.json';original=json.loads(cp.read_text());checks={name:gate(result,original['metrics'][name]) for name in ['previous_native','raw_min_on']};passed=all(x['pass_primary_gate'] for x in checks.values());secondary=gate(result,unprojected[case]['metrics']);rows.append(dict(case=case,iteration=p['iteration'],metrics=result,checks=checks,pass_both_controls=passed,secondary_vs_unprojected_live_prefix=secondary,clipped_resources=p['clipped_resources'],positive_excess_for_existing_consumer=sum(max(0,ledger[n]-r['capacity']) for n,r in forecast.items())));print('CAPACITY_PROJECTION_GATE',case,passed,flush=True)
  for q in [proof,Path(p['score_file']),spec,dp,rp,bp,label,cp]:bindings[str(q)]=sha(q)
 assert checked==12 and len(rows)==9 and all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,independent_metric_vectors=checked,passed_available_cases=sum(x['pass_both_controls'] for x in rows),available_cases=6,required_cases=9,full9_gate=False,bindings=bindings,scope='Capacity-range score forecast at unchanged live readiness iteration, not a path-consistent native ledger or legal route. Original full-domain/ties/two controls/four metrics unchanged. Existing positive-excess preload becomes identically zero for this bounded forecast, so it does not establish native utility. Exposed development only, unavailable width96 cases retained; no fullpaid/unseen gain.'),indent=2,default=lambda x:dict(numerator=x.numerator,denominator=x.denominator))+'\n')
if __name__=='__main__':main()
