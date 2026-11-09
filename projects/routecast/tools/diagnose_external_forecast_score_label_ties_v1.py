"""Fixed six-model all3 score/label and tie diagnostic; original gates untouched."""
import json,sys
from pathlib import Path
from collections import Counter
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from external_forecast_metrics_v1 import vectors
from forecast_topk_tie_diagnostic_v1 import diagnose
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'prospective_external_family_supplementary_development_v1_2026-10-19';O=E/'prospective_external_family_score_label_tie_diagnosis_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);cp=E/'forecast_topk_tie_diagnostic_contract_v1_2026-10-19/verification.json';c=read(cp);assert all(sha(p)==h for p,h in c['bindings'].items());bindings[str(cp)]=sha(cp);cases=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';sp=P/'specifications'/case/'comparison_spec.json';s=read(sp);comparison=Path(s['predictions']['native_retained_on']['frame']).parent.parent/'comparison.json';arms=[dict(name='previous_native',frame=s['source_frame'],proof=s['source_proof'],comparison=str(comparison),method='previous_native')]
  for name,key in [('raw_min_on','raw_min_on'),('all_NET_feedback','native_retained_on')]:arms.append(dict(name=name,frame=s['predictions'][key]['frame'],proof=s['predictions'][key]['proof'],comparison=str(comparison),method=key))
  for name,directory in [('zero_feedback_warm','zero_feedback_warm'),('endpoint_local','endpoint_local_feedback'),('verified_tree_overlay','verified_tree_forecast_overlay')]:
   d=E/f'prospective_external_family_{directory}_v1_2026-10-19';spec=read(d/case/'comparison_spec.json');arm=spec['predictions']['native_retained_on'];arms.append(dict(name=name,frame=arm['frame'],proof=arm['proof'],comparison=str(d/case/'comparison.json'),method='native_retained_on'))
  for arm in arms:
   proof=read(arm['proof']);assert all(sha(p)==h for p,h in proof['bindings'].items());assert proof['bindings'][arm['frame']]==sha(arm['frame'])
   for p in [Path(arm['frame']),Path(arm['proof']),Path(arm['comparison'])]:bindings[str(p)]=sha(p)
  cases.append(dict(case=case,domain_proof=s['domain_proof'],domain_independent_proof=s['domain_independent_proof'],label_proof=s['label_proof'],label_physical_audit=s['label_physical_audit'],arms=arms))
  for p in [sp,Path(s['domain_proof']),Path(s['domain_independent_proof']),Path(s['label_proof']),Path(s['label_physical_audit'])]:bindings[str(p)]=sha(p)
 pp=O/'protocol.json';pp.write_text(json.dumps(dict(cases=cases,bindings=bindings,policy='Fixed diagnostic for all3 cases and six already evaluated predictors, original full CHANNEL/spatial domains and K unchanged. Report score ranges, native legal capacity and topK boundary ties, plus expected overlap for INDEPENDENT uniform valid tie selections. This expectation is NOT a gate, and identical perfectly tied score vectors need not give1. No new model, threshold/NET selection, label transformation, metric replacement or promotion.'),indent=2)+'\n');bindings[str(pp)]=sha(pp);rows=[]
 for spec in cases:
  dp=Path(spec['domain_proof']);domain=read(dp);resources=[json.loads(s) for s in (dp.parent/'resources.jsonl').read_text().splitlines()];bins=read(dp.parent/'spatial_bins.json');labelproof=read(spec['label_proof']);assert all(sha(p)==h for p,h in labelproof['bindings'].items());assert labelproof['bindings'][spec['label_physical_audit']]==sha(spec['label_physical_audit']);physical=read(spec['label_physical_audit']);native={int(n):v for n,v in physical['node_occupancy'].items()};truth=vectors(resources,bins,native,domain['graph_nodes'],truth=True);assert all(native.get(r['id'],0)<=r['capacity'] for r in resources)
  for arm in spec['arms']:
   f=read(arm['frame']);ledger={int(n):v for n,v in f['ledger'].items()};pred=vectors(resources,bins,ledger,domain['graph_nodes']);published=read(arm['comparison'])['metrics'][arm['method']]
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
    result=diagnose(pred[scope],truth[scope],k);assert result['fixed_ID_hits']==published[scope]['top_k_hits'];row=dict(case=spec['case'],method=arm['name'],scope=scope,**result,truth_positive=sum(v>0 for v in truth[scope].values()),predicted_over_capacity_resources=sum(ledger.get(r['id'],0)>r['capacity'] for r in resources));rows.append(row)
    print('SCORE_LABEL_TIE',json.dumps({k:row[k] for k in ['case','method','scope','truth','prediction','fixed_ID_hits','truth_distinct_scores','independent_uniform_tie_expected_precision']}),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(status='ALL36_FIXED_SCORE_LABEL_TIE_DIAGNOSTICS_PREPARED',rows=rows,bindings=bindings,original_quality_gates_changed=False,scope='Already exposed development diagnosis only; independent tie expectation not an acceptance criterion or scientifically calibrated probability. No new routing or performance claim.'),indent=2)+'\n')
if __name__=='__main__':main()
