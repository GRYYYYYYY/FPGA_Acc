"""Review complete primitive correctness and retain all local negative costs."""
import json,sys,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
bindings={str(Path(__file__)):sha(Path(__file__))};rows=[]
def auth(d):
 for section in ['bindings','files']:
  for p,h in d.get(section,{}).items():
   assert sha(p)==h,p
   if p in bindings:assert bindings[p]==h
   bindings[p]=h
for name,nets in [('xtea',1029),('mmc',48634)]:
 D=R/'experiments/real_rr_reverse_single_sink_v1_2026-10-08'/name
 r=json.loads((D/'receipt.json').read_text());v=json.loads((D/'verification.json').read_text());g=json.loads((D/'budget_gate_diagnosis_v1.json').read_text())
 for data in [r,v,g]:auth(data)
 for f in ['receipt.json','protocol.json','verification.json','budget_gate_diagnosis_v1.json']:bindings[str(D/f)]=sha(D/f)
 assert v['complete_single_target_primitive_pass']
 assert all([row['phase'] for row in d['rows']]==['initial','round0','round1'] for d in [r,v,g])
 phases=[]
 for x,y,z in zip(r['rows'],v['rows'],g['rows']):
  assert x['complete_nets']==z['complete_nets']==nets and y['physical_paths_checked']==2*nets
  assert x['all_minimum_objectives_equal'] and y['all_original_XML_fraction_RC_and_forward_destination_price_checks_pass']
  assert x['changed_equal_objective_paths']==y['changed_equal_objective_paths']
  assert sum(z['budget_gate_pairs'].values())==nets and sum(z['candidate_raw_delay_changes'].values())==nets
  assert all(math.isfinite(x[k]) and x[k]>0 for k in ['baseline_seconds','candidate_seconds'])
  phases.append(dict(phase=x['phase'],baseline_seconds=x['baseline_seconds'],candidate_seconds=x['candidate_seconds'],candidate_over_baseline=x['candidate_seconds']/x['baseline_seconds'],changed_equal_objective_paths=x['changed_equal_objective_paths'],budget_gate_pairs=z['budget_gate_pairs'],candidate_raw_delay_changes=z['candidate_raw_delay_changes']))
 baseline=sum(x['baseline_seconds'] for x in phases);candidate=sum(x['candidate_seconds'] for x in phases)
 assert math.isfinite(r['reverse_setup_seconds']) and r['reverse_setup_seconds']>=0
 rows.append(dict(name=name,complete_single_target_nets=nets,phases=phases,baseline_query_total_seconds=baseline,candidate_query_total_seconds=candidate,reverse_setup_seconds=r['reverse_setup_seconds'],candidate_query_plus_reverse_setup_over_baseline_query=(candidate+r['reverse_setup_seconds'])/baseline,all_three_observed_candidate_query_times_slower=all(x['candidate_over_baseline']>1 for x in phases)))
assert all(sha(p)==h for p,h in bindings.items())
D=R/'experiments/real_rr_reverse_primitive_review_v1_2026-10-08';D.mkdir(exist_ok=False)
(D/'review.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,complete_two_case_primitive_evidence_authenticated=True,scope='Complete original single-target subsets only, frozen old development prices, independently audited physical costs and counterfactual budgets. Single forward-then-reverse timing per phase; setup separately shown, graph/price-context prep/full mixed model/feedback/native excluded. No paired statistical stability, unseen-family, full-model QoR or complete workflow conclusion. Negative local costs retained; not adopted as transparent speed replacement.'),indent=2)+'\n')
print(json.dumps([{k:v for k,v in row.items() if k!='phases'} for row in rows],indent=2))
