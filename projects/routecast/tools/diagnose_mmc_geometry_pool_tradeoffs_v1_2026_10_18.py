"""Report fixed gate failures, MAE/rank tradeoffs and existing truth tie bounds."""
import json,sys
from pathlib import Path
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 proof=R/'experiments/mmc_geometry_pool_verification_v1_2026-10-18/verification.json';v=json.loads(proof.read_text());assert v['status']=='pass'
 root=R/'experiments/mmc_geometry_pool_quality_v1_2026-10-18';rows=[];bindings={str(proof):sha(proof),**closure([Path(__file__)])}
 for case in ['case_01','case_02','case_03']:
  path=root/(case+'.json');assert v['bindings'][str(path)]==sha(path);bindings[str(path)]=sha(path)
  data=json.loads(path.read_text());m=data['metrics']['cold'];ties=data['tie_diagnostics']['cold'];metrics={}
  for name in ['native_retained_on','pooled_native_retained_on','previous_native']:
   c=m[name]['concrete'];d=ties[name]['concrete'];k=c['k'];slots=d['truth_slots_from_tie'];above=d['truth_strictly_above'];equal=d['truth_equal_boundary']
   assert c['truth_k_boundary']==1 and above==0 and slots==k and equal==c['nonzero_truth']
   # Here all positive truth nodes share the maximum value; upper overlap is
   # exactly the number of predicted topK resources in the full positive set.
   within=d['fixed_prediction_truth_tie_max_hits'];assert within<=k
   metrics[name]=dict(spearman=c['spearman'],fixed_ID_tie_precision_at_k=c['precision_at_k'],mae=c['mae'],truth_equal_maximum_resources=equal,k=k,allowed_truth_tie_precision_interval=[d['fixed_prediction_truth_tie_min_hits']/k,within/k],expected_precision_if_truth_tie_subset_uniform=str(Fraction(slots*within,equal*k)),scope='Tie interval and uniform-subset expectation are retrospective diagnostics, not replacement gates or a new hotspot truth definition.')
  rows.append(dict(case=case,metrics=metrics,primary_all_controls_pass=all(c['pass_primary_gate'] for c in data['primary_checks'] if c['label']=='cold'),MAE_degraded_independently_of_truth_topK_tie=m['pooled_native_retained_on']['concrete']['mae']>m['native_retained_on']['concrete']['mae']))
 out=R/'experiments/mmc_geometry_pool_verification_v1_2026-10-18/tradeoff_diagnosis_v1.json'
 with out.open('x') as stream:json.dump(dict(status='complete',bindings=bindings,rows=rows,scope='Existing fixed Precision@K remains authoritative and failed. Native final legal unit-channel occupancy has a large binary top-value tie. Pooling changes the ordering relative to the fixed ID-selected truth subset; MAE also worsens, so ambiguity does not explain all accuracy tradeoffs. No promotion, changed gate, native run or heldout claim.'),stream,indent=2)
 print('GEOMETRY POOL TRADEOFFS RECORDED',flush=True)

if __name__=='__main__':main()
