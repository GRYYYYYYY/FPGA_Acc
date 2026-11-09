"""Independent pair completeness and parent-key DAG membership/mode audit."""
from pathlib import Path
from collections import defaultdict,Counter
import json,hashlib,math
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_missing_owner_DAG_diagnosis_v1_2026-10-19';review=O/'review.json';doc=json.loads(review.read_text());original=R/'experiments/mmc_forecast_owner_support_diagnosis_v1_2026-10-19/review.json';old=json.loads(original.read_text());labels={};needed=defaultdict(list);groups=[];bindings={str(p):sha(p) for p in [review,original,Path(__file__).resolve()]}
 for row in doc['rows']:
  base=next(x for x in old['rows'] if all(x[k]==row[k] for k in ['case','arm','phase']));p=Path(base['per_resource']);assert sha(p)==old['bindings'][str(p)];expected={(x['node'],net) for x in map(json.loads,p.read_text().splitlines()) for nets in x['actual_pair_partition'].values() for net in nets};seen=set();stages=Counter();modes=defaultdict(Counter);output=Path(row['per_pair']);assert sha(output)==doc['bindings'][str(output)]
  for line in output.open():
   x=json.loads(line);pair=x['node'],x['net_id'];assert pair in expected and pair not in seen;seen.add(pair);key=row['case'],x['net_id'],x['node'];value=x['model_mode'],x['support_stage'];assert key not in labels or labels[key]==value;labels[key]=value;stages[x['support_stage']]+=1;modes[x['model_mode']][x['support_stage']]+=1
  assert seen==expected and dict(stages)==row['stage_counts'] and {k:dict(v) for k,v in modes.items()}==row['mode_counts'];groups.append({k:row[k] for k in ['case','arm','phase','actual_pairs']});bindings[str(output)]=sha(output);bindings[str(p)]=sha(p)
 wanted=defaultdict(dict)
 for (case,net,node),value in labels.items():wanted[case,net][node]=value
 for case in ['episode_01','episode_02','episode_03']:
  ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json';meta=json.loads(ep.read_text());nets=sorted({q['net_id'] for q in meta['connections']});ip=R/f'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/{case}/NET_contribution_indices.json';indices=json.loads(ip.read_text());assert len(indices)==len(nets)==55300
  for net,index in zip(nets,indices):
   if (case,net) in wanted:needed[index].append((case,net))
  for p in [ep,ip]:assert sha(p)==doc['bindings'][str(p)];bindings[str(p)]=sha(p)
 bank=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/NET_contributions.jsonl';assert sha(bank)==doc['bindings'][str(bank)];verified=0
 for line in bank.open():
  x=json.loads(line)
  if x['index'] not in needed:continue
  choices=x['support_choices'];dag={int(n) for n in choices}|{x['source']};prob={int(n) for n,v in x['probabilities'].items() if int(v.split('/')[0])>0};assert prob<=dag
  mode='exact_single_sink' if len(x['sinks'])==1 else 'exact_multi_sink_local_parents' if math.prod(len(v) for v in choices.values())<=4096 else 'sampled_shared_parent_multi_sink';assert mode==x['mode']
  for case,net in needed[x['index']]:
   assert net==x['net_id']
   for node,expected in wanted[case,net].items():
    stage='probability_supported' if node in prob else 'DAG_supported_probability_absent' if node in dag else 'outside_model_DAG';assert expected==(mode,stage);verified+=1
 assert verified==len(labels);bindings[str(bank)]=sha(bank)
 (O/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL18_PAIR_COMPLETENESS_PARENT_KEY_DAG_MEMBERSHIP_AND_MODE_COUNTS_PASS','unique_case_NET_resource_pairs_verified':verified,'rows':groups,'bindings':bindings,'scope':'Archived model DAG identity, not proof that a native path has worse electrical delay; no sampled-seed or policy adjustment.'},indent=2)+'\n');print('INDEPENDENT_DAG_PASS',verified,'unique pairs')
if __name__=='__main__':main()
