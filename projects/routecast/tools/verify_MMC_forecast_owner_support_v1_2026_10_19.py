"""Independent pair-index membership and integer-common-denominator mass audit."""
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
from math import gcd
import json,hashlib
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def rational(s):
 w=s.split('/');assert len(w) in (1,2);a=int(w[0]);b=int(w[1]) if len(w)==2 else 1;assert b>0;return a,b
def main():
 O=R/'experiments/mmc_forecast_owner_support_diagnosis_v1_2026-10-19';proof=O/'review.json';doc=json.loads(proof.read_text());assert len(doc['rows'])==18;assert not (O/'independent_verification_v1.json').exists();bank=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/NET_contributions.jsonl';assert sha(bank)==doc['bindings'][str(bank)];needed=defaultdict(list);targets={};chosen={};pair_support={};mass={};bindings={str(proof):sha(proof),str(bank):sha(bank),str(Path(__file__).resolve()):sha(__file__)}
 for case in ['episode_01','episode_02','episode_03']:
  ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json';meta=json.loads(ep.read_text());nets=sorted({q['net_id'] for q in meta['connections']});ix=R/f'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/{case}/NET_contribution_indices.json';indices=json.loads(ix.read_text());assert len(indices)==len(nets)==55300;cp=R/f'experiments/mmc_preferred_NET_claims_v1_2026-10-19/{case}/claims.jsonl';chosen[case]={x['node']:x['preferred_net'] for x in map(json.loads,cp.read_text().splitlines())};targets[case]=set(chosen[case]);mass[case]={n:(0,1) for n in targets[case]};pair_support[case]=set()
  for index,net in zip(indices,nets):needed[index].append((case,net))
  for p in [ep,ix,cp]:assert sha(p)==doc['bindings'][str(p)];bindings[str(p)]=sha(p)
 for line in bank.open():
  row=json.loads(line)
  for case,net in needed.get(row['index'],[]):
   assert net==row['net_id']
   for key,value in row['probabilities'].items():
    n=int(key)
    if n not in targets[case]:continue
    a,b=rational(value);assert 0<a<=b;pair=(n,net);assert pair not in pair_support[case];pair_support[case].add(pair);old,den=mass[case][n];common=den//gcd(den,b)*b;total=old*(common//den)+a*(common//b);factor=gcd(total,common);mass[case][n]=(total//factor,common//factor)
 results=[]
 for row in doc['rows']:
  case=row['case'];actual_file=R/f"experiments/mmc_preferred_resource_competition_diagnosis_v1_2026-10-19/{case}_{row['arm']}_{row['phase']}.jsonl";actual={x['node']:x['actual_NETs'] for x in map(json.loads,actual_file.read_text().splitlines())};counts=Counter();totalmass=Fraction();absolute=Fraction();square=Fraction();seen=set();file=Path(row['per_resource'])
  for line in file.open():
   record=json.loads(line);node=record['node'];assert node not in seen;seen.add(node);owners=actual[node];partition={k:[] for k in ['chosen','supported_nonchosen','outside_forecast_support']}
   for net in owners:partition['chosen' if net==chosen[case][node] else 'supported_nonchosen' if (node,net) in pair_support[case] else 'outside_forecast_support'].append(net)
   assert record['actual_pair_partition']==partition and record['actual_owner_count']==len(owners);a,b=mass[case][node];expected=Fraction(a,b);assert Fraction(record['predicted_owner_mass'])==expected;totalmass+=expected;error=expected-len(owners);absolute+=abs(error);square+=error*error
   counts.update({k:len(v) for k,v in partition.items()});counts['actual_pairs']+=len(owners);counts['used_resources']+=bool(owners);counts['unused_resources']+=not owners;counts['resources_with_outside_support_owner']+=bool(partition['outside_forecast_support'])
  assert seen==targets[case] and dict(counts)==row['totals'];assert totalmass==Fraction(row['predicted_owner_mass']) and absolute==Fraction(row['sum_absolute_owner_count_error']) and square==Fraction(row['sum_squared_owner_count_error']);results.append({'case':case,'arm':row['arm'],'phase':row['phase'],'exact_owner_partitions':len(seen),'exact_integer_mass_and_errors_verified':True});bindings[str(file)]=sha(file);bindings[str(actual_file)]=sha(actual_file);print('SUPPORT_INDEPENDENT_PASS',case,row['arm'],row['phase'],flush=True)
 (O/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL18_SUPPORT_PAIR_MEMBERSHIP_INTEGER_MASS_AND_ERROR_SUMS_PASS','rows':results,'bindings':bindings,'scope':'Supports owner partition and resource mass/error sums; probability-on-actual-pairs auxiliary field not independently checked. Risk-selected exposed diagnostic only, no fitted model or native policy.'},indent=2)+'\n')
if __name__=='__main__':main()
