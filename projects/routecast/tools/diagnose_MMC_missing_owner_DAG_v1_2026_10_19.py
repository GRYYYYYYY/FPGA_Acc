"""Exposed native pairs versus frozen lexicographic model DAG and sampled support."""
from pathlib import Path
from collections import defaultdict,Counter
import json,hashlib
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_missing_owner_DAG_diagnosis_v1_2026-10-19';O.mkdir(exist_ok=False);B=R/'experiments/mmc_forecast_owner_support_diagnosis_v1_2026-10-19';verified=B/'independent_verification_v1.json';assert json.loads(verified.read_text())['status']=='ALL18_SUPPORT_PAIR_MEMBERSHIP_INTEGER_MASS_AND_ERROR_SUMS_PASS';review=B/'review.json';d=json.loads(review.read_text());wanted=defaultdict(lambda:defaultdict(set));needed=defaultdict(list);identities={};bindings={str(p):sha(p) for p in [verified,review,Path(__file__).resolve()]}
 protocol={'scope':'Offline exposed positive-risk CHANNEL diagnosis only. DAG means the archived model minimum additive-cost then minimum-hop support, not every legal route, every RC-equivalent path, or a globally feasible NET assignment.','stages':['probability_supported','DAG_supported_probability_absent','outside_model_DAG'],'mode_groups':['exact_single_sink','exact_multi_sink_local_parents','sampled_shared_parent_multi_sink'],'no_new_prediction_or_policy':True};(O/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 for row in d['rows']:
  case=row['case'];p=Path(row['per_resource']);assert sha(p)==d['bindings'][str(p)]
  for x in map(json.loads,p.read_text().splitlines()):
   for group in x['actual_pair_partition'].values():
    for net in group:wanted[case][net].add(x['node'])
  bindings[str(p)]=sha(p)
 for case in wanted:
  ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json';meta=json.loads(ep.read_text());nets=sorted({q['net_id'] for q in meta['connections']});idx=R/f'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/{case}/NET_contribution_indices.json';indices=json.loads(idx.read_text());assert len(nets)==len(indices)==55300
  for net,index in zip(nets,indices):
   if net in wanted[case]:needed[index].append((case,net))
  for p in [ep,idx]:bindings[str(p)]=sha(p)
 bank=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/NET_contributions.jsonl';assert sha(bank)==d['bindings'][str(bank)];bindings[str(bank)]=sha(bank)
 for line in bank.open():
  x=json.loads(line)
  for case,net in needed.get(x['index'],[]):
   assert net==x['net_id'];dag=set(map(int,x['support_distance']));prob=set(map(int,x['probabilities']));assert prob<=dag;assert set(map(int,x['support_choices']))==dag-{x['source']}
   for node in wanted[case][net]:
    key=(case,net,node);assert key not in identities;identities[key]=(x['mode'],'probability_supported' if node in prob else 'DAG_supported_probability_absent' if node in dag else 'outside_model_DAG')
 rows=[]
 for row in d['rows']:
  case=row['case'];counts=Counter();by_mode=defaultdict(Counter);target=O/f"{case}_{row['arm']}_{row['phase']}.jsonl"
  with target.open('x') as f:
   for x in map(json.loads,Path(row['per_resource']).read_text().splitlines()):
    for old_category,nets in x['actual_pair_partition'].items():
     for net in nets:
      mode,stage=identities[case,net,x['node']];assert (old_category=='outside_forecast_support')==(stage!='probability_supported');counts[stage]+=1;by_mode[mode][stage]+=1;f.write(json.dumps({'node':x['node'],'net_id':net,'model_mode':mode,'support_stage':stage},separators=(',',':'))+'\n')
  assert sum(counts.values())==row['totals']['actual_pairs'];missing=counts['DAG_supported_probability_absent']+counts['outside_model_DAG'];assert missing==row['totals']['outside_forecast_support'];rows.append({'case':case,'arm':row['arm'],'phase':row['phase'],'actual_pairs':sum(counts.values()),'stage_counts':dict(counts),'mode_counts':{k:dict(v) for k,v in by_mode.items()},'outside_DAG_fraction_of_missing':counts['outside_model_DAG']/missing if missing else None,'per_pair':str(target)});bindings[str(target)]=sha(target);print('DAG_MISSING',case,row['arm'],row['phase'],dict(counts),flush=True)
 (O/'review.json').write_text(json.dumps({'status':'ALL18_MISSING_OWNER_MODEL_DAG_DECOMPOSITION_PRODUCED','rows':rows,'bindings':bindings,'scope':protocol['scope'],'independent_verification_pending':True},indent=2)+'\n')
if __name__=='__main__':main()
