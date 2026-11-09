"""Same forecast gates on paid native partial occupancy, independent metrics replay."""
import json
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter
from pre_route_endpoints import sha
from external_forecast_metrics_v1 import vectors,metrics,gate
from audit_prince_forecast_metrics_v1 import check
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_native_first_iteration_quality_v1_2026-10-20'
def encode(x):return json.loads(json.dumps(x,default=lambda v:dict(numerator=v.numerator,denominator=v.denominator)))
def main():
 D.mkdir(exist_ok=False);root=E/'prince_native_first_iteration_trial_v1_2026-10-20';vp=root/'verification.json';v=json.loads(vp.read_text());oldp=E/'prince_feedback_quality_v1_2026-10-20/verification.json';old=json.loads(oldp.read_text());available={x['case']:x for x in old['rows']};bindings={str(p):sha(p) for p in [vp,oldp,Path(__file__)]};rows=[];checked=0
 for row in v['rows']:
  case=row['case'];d=root/case;receipt=json.loads((d/'receipt.json').read_text());assert all(sha(p)==h for p,h in receipt['files'].items());bindings[str(d/'receipt.json')]=sha(d/'receipt.json')
  if case not in available:rows.append(dict(case=case,status='UNAVAILABLE_FINAL_LEGAL_LABEL',pass_case_gate=False));continue
  assert row['independent_tree_endpoint_audit_pass'];cp=Path(available[case]['comparison']);original=json.loads(cp.read_text());spec=json.loads((cp.parent/'specification.json').read_text());dp=Path(spec['domain_proof']);domain=json.loads(dp.read_text());rp=dp.parent/'resources.jsonl';bp=dp.parent/'spatial_bins.json';resources=list(map(json.loads,rp.open()));bins=json.loads(bp.read_text());physical=d/'physical_audit.json';label=Path(spec['label_physical_audit']);prediction={int(n):c for n,c in json.loads(physical.read_text())['node_occupancy'].items()};truth={int(n):c for n,c in json.loads(label.read_text())['node_occupancy'].items()};result=metrics(vectors(resources,bins,prediction,domain['graph_nodes']),vectors(resources,bins,truth,domain['graph_nodes'],truth=True),domain['resource_k'],domain['spatial_k']);coded=encode(result)
  # Independent transposed bin sums and doubled integer rank/group-set comparisons.
  adj={tuple(b['key']):[] for b in bins}
  for r in resources:
   for key in r['bins']:adj[tuple(key)].append(r['id'])
  def normalize(ledger):return dict(resource={r['id']:Q(ledger.get(r['id'],0),r['capacity']) for r in resources},spatial={tuple(b['key']):Q(sum(ledger.get(n,0) for n in adj[tuple(b['key'])]),b['capacity']) for b in bins})
  a,b=normalize(prediction),normalize(truth)
  for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:check(a[scope],b[scope],k,coded[scope]);checked+=1
  controls={c:gate(result,original['metrics'][c]) for c in ['previous_native','raw_min_on']};rowout=dict(case=case,status='PAID_FIRST_ITER_FORECAST_COMPARED',metrics=result,checks=controls,pass_case_gate=all(c['pass_primary_gate'] for c in controls.values()),overflow_units=row['overflow_units'],native_seconds=row['native_seconds'],paid_stage_seconds=row['paid_stage_seconds']);rows.append(rowout)
  for p in [cp,dp,rp,bp,physical,label]:bindings[str(p)]=sha(p)
  print('FIRST_ITER_GATE',case,rowout['pass_case_gate'],flush=True)
 assert checked==12 and all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,independently_reconciled_metric_vectors=checked,passed_case_gates=sum(r['pass_case_gate'] for r in rows),required_target_cases=9,full9_gate=False,scope='Paid single-native-iteration development baseline against same final cold native labels and original previous_native/raw_min_on controls. Partial congestion retained. Width96 final legal labels unavailable, full9 gate false. No unseen, physical timing or complete matched workflow gain.'),indent=2,default=lambda x:dict(numerator=x.numerator,denominator=x.denominator))+'\n')
if __name__=='__main__':main()
