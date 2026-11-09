"""Frozen forecast support versus exposed native owner identities; risk-set conditional."""
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
import json,hashlib
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_forecast_owner_support_diagnosis_v1_2026-10-19';O.mkdir(exist_ok=False);base=R/'experiments/mmc_preferred_resource_competition_diagnosis_v1_2026-10-19';proof=base/'independent_verification_v1.json';assert json.loads(proof.read_text())['status']=='ALL18_RESOURCE_OWNER_SETS_AND_CATEGORIES_INDEPENDENTLY_VERIFIED';doc=json.loads((base/'review.json').read_text());receipt=R/'experiments/mmc_preferred_NET_claims_v1_2026-10-19/receipt.json';old=json.loads(receipt.read_text());bank=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/NET_contributions.jsonl';assert sha(bank)==old['bindings'][str(bank)];needed=defaultdict(list);claims={};support={};bindings={str(p):sha(p) for p in [proof,base/'review.json',receipt,bank,Path(__file__).resolve()]}
 (O/'protocol.json').write_text(json.dumps({'scope':'Posthoc18 exposed arm/phase risk-set conditional diagnostic. No all-graph accuracy, probability calibration, fitted weights, causal claim or new policy selection. Same fixed forecast for all three native arms.','owner_pair_categories':['chosen','supported_nonchosen','outside_forecast_support'],'required_sums':'All actual NET/resource pairs partition exactly; per-resource probability sum conserved.'},indent=2)+'\n')
 for case in ['episode_01','episode_02','episode_03']:
  ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json';meta=json.loads(ep.read_text());eligible=sorted({q['net_id'] for q in meta['connections']});idx=R/f'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/{case}/NET_contribution_indices.json';indices=json.loads(idx.read_text());assert len(indices)==len(eligible)==55300
  cp=R/f'experiments/mmc_preferred_NET_claims_v1_2026-10-19/{case}/claims.jsonl';claims[case]={x['node']:x for x in map(json.loads,cp.read_text().splitlines())};support[case]={n:{} for n in claims[case]}
  for n,i in zip(eligible,indices):needed[i].append((case,n))
  for p in [ep,idx,cp]:assert sha(p)==old['bindings'][str(p)];bindings[str(p)]=sha(p)
 for line in bank.open():
  record=json.loads(line)
  for case,net in needed.get(record['index'],[]):
   assert record['net_id']==net
   for key,value in record['probabilities'].items():
    node=int(key)
    if node in support[case]:
     probability=Fraction(value);assert 0<probability<=1 and net not in support[case][node];support[case][node][net]=probability
 for case in claims:
  for node,c in claims[case].items():assert len(support[case][node])==c['candidates'] and support[case][node][c['preferred_net']]==Fraction(c['probability'])
 rows=[]
 for source in doc['rows']:
  case=source['case'];fp=Path(source['per_resource']);totals=Counter();mass=Fraction();absolute=Fraction();squared=Fraction();pair_probability=Fraction();target=O/f"{case}_{source['arm']}_{source['phase']}.jsonl"
  with target.open('x') as out:
   for line in fp.open():
    x=json.loads(line);node=x['node'];pred=support[case][node];actual=x['actual_NETs'];chosen=claims[case][node]['preferred_net'];categories={'chosen':[],'supported_nonchosen':[],'outside_forecast_support':[]}
    for net in actual:categories['chosen' if net==chosen else 'supported_nonchosen' if net in pred else 'outside_forecast_support'].append(net)
    for key,values in categories.items():totals[key]+=len(values)
    totals['actual_pairs']+=len(actual);totals['used_resources']+=bool(actual);totals['unused_resources']+=not actual;totals['resources_with_outside_support_owner']+=bool(categories['outside_forecast_support'])
    expected=sum(pred.values(),Fraction());error=expected-len(actual);mass+=expected;absolute+=abs(error);squared+=error*error;pair_probability+=sum((pred.get(net,Fraction()) for net in actual),Fraction())
    out.write(json.dumps({'node':node,'predicted_owner_mass':str(expected),'actual_owner_count':len(actual),'actual_pair_partition':categories},separators=(',',':'))+'\n')
  assert totals['actual_pairs']==sum(totals[k] for k in ['chosen','supported_nonchosen','outside_forecast_support'])==source['total_NET_resource_pairs'];rows.append({'case':case,'arm':source['arm'],'phase':source['phase'],'resources':source['resources'],'totals':dict(totals),'predicted_owner_mass':str(mass),'sum_absolute_owner_count_error':str(absolute),'sum_squared_owner_count_error':str(squared),'sum_probability_on_actual_owner_pairs':str(pair_probability),'supported_pair_fraction':(totals['chosen']+totals['supported_nonchosen'])/totals['actual_pairs'],'per_resource':str(target)});bindings[str(fp)]=sha(fp);bindings[str(target)]=sha(target);print('OWNER_SUPPORT',case,source['arm'],source['phase'],dict(totals),flush=True)
 (O/'review.json').write_text(json.dumps({'status':'ALL18_FROZEN_FORECAST_OWNER_SUPPORT_AND_MASS_DIAGNOSTICS_COMPLETE','rows':rows,'bindings':bindings,'scope':'Conditional on frozen positive-risk unit CHANNEL resources, not all-graph prediction gate or calibrated ownership probability. No retraining or policy tuning. Independent support membership verification pending.'},indent=2)+'\n')
if __name__=='__main__':main()
