"""Exact input signature collisions in existing linear resource-category scoring."""
import json,array
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def ar(p,t):
 a=array.array(t);a.frombytes(p.read_bytes());return a

def main():
 out=R/'experiments/mmc_owner_signature_ambiguity_v1_2026-10-19';out.mkdir(exist_ok=False);cp=R/'experiments/mmc_resource_context_v1_2026-10-19/CHANNEL_ids.u32';ids=ar(cp,'I');channels=set(ids);priorp=R/'experiments/mmc_owner_NET_gain_diagnosis_v1_2026-10-19/results.json';prior=read(priorp);bindings={str(p):sha(p) for p in [cp,priorp,Path(__file__).resolve()]};rows=[]
 for item in prior['rows']:
  case=item['case'];ctx=R/f'experiments/mmc_resource_owner_context_v1_2026-10-19/{case}.u16';codes=dict(zip(ids,ar(ctx,'H')));bp=R/f'experiments/mmc_candidate_ownership_implications_v1_2026-10-19/{case}/banks.jsonl';assert sha(bp)==prior['bindings'][str(bp)];banks={b['net_id']:(set(b['A']),set(b['B'])) for b in map(json.loads,bp.open())};A=Counter(n for a,b in banks.values() for n in a);B=Counter(n for a,b in banks.values() for n in b);safe={n for n in channels if A[n]<=1 and B[n]<=1};groups=defaultdict(list)
  # Input-only exact score basis: coefficient per frozen category is arbitrary.
  for net,(a,b) in banks.items():
   delta=Counter(codes[n] for n in (a-b)&safe);delta.subtract(codes[n] for n in (b-a)&safe);signature=tuple(sorted((c,d) for c,d in delta.items() if d));groups[signature].append(net)
  root=R/f'experiments/mmc_owner_frequency_development_v1_2026-10-19/{case}';mp=root/'model.json';m=read(mp);choicep=root/'choices.jsonl';oraclep=R/f'experiments/mmc_aggregate_L1_oracle_v1_2026-10-19/{case}/choices.jsonl'
  for p in [choicep,oraclep]:assert sha(p)==prior['bindings'][str(p)]
  choices={c['net_id']:c for c in map(json.loads,choicep.open())};oracle={c['net_id']:c for c in map(json.loads,oraclep.open())};assert set(choices)==set(oracle)==set(banks);stats=Counter();ambiguous=[];collision_loss=0;signature_rows=[]
  for sig,nets in groups.items():
   expected=sum(d*(10**6-2*m['probability_int'][c]) for c,d in sig);assert all(choices[n]['expected_gain_scaled']==expected for n in nets);pos=[n for n in nets if oracle[n]['aggregate_gain']>0];neg=[n for n in nets if oracle[n]['aggregate_gain']<0];stats['signatures']+=1;stats['NETs']+=len(nets);stats['zero_signature_NETs']+=len(nets) if not sig else 0
   if len(nets)>1:stats['colliding_NETs']+=len(nets);stats['colliding_signatures']+=1
   if pos and neg:
    stats['mixed_sign_signatures']+=1;stats['mixed_sign_NETs']+=len(nets);harmful=[n for n in neg if choices[n]['pick']=='B' and expected>0];stats['harmful_positive_selected_in_mixed_signatures']+=len(harmful);ambiguous.extend(nets)
   benefit=sum(max(0,oracle[n]['aggregate_gain']) for n in nets);harm=sum(max(0,-oracle[n]['aggregate_gain']) for n in nets);collision_loss+=min(benefit,harm)
   signature_rows.append(dict(signature=sig,NETs=nets,positive=len(pos),negative=len(neg),zero=len(nets)-len(pos)-len(neg),true_benefit=benefit,true_harm=harm,predicted_gain_scaled=expected))
  assert stats['NETs']==55300;assert sum(len(v) for v in groups.values())==len(set(n for ns in groups.values() for n in ns))==55300
  totalharm=item['groups']['selected_positive_predicted']['negative_actual_NETs'];assert stats['harmful_positive_selected_in_mixed_signatures']<=totalharm;row=dict(case=case,stats=dict(stats),harmful_positive_selected_total=totalharm,unconstrained_same_signature_uniform_action_regret=collision_loss,scope='Identical signature forces identical linear category-score for arbitrary category probabilities. Dependency graph and other inputs can still distinguish decisions; uniform-action regret is a hypothetical unconstrained comparator, NOT a bound on actual closed chooser or full rank metrics.')
  target=out/(case+'.signatures.jsonl')
  with target.open('x') as f:
   for s in signature_rows:f.write(json.dumps(s,separators=(',',':'))+'\n')
  rows.append(row);bindings.update({str(p):sha(p) for p in [ctx,bp,mp,choicep,oraclep,target]});print(case,dict(stats),'uniform_action_regret',collision_loss,flush=True)
 with (out/'results.json').open('x') as f:json.dump(dict(status='ALL3_EXACT_INPUT_SIGNATURES_SCORE_EQUALITIES_AND_LABEL_AMBIGUITY_ACCOUNTED',rows=rows,bindings=bindings,scope='Posthoc exposed-data representation audit. No model fitting or score changes; labels accessed only after input grouping. No family/native utility claim.'),f,indent=2)
if __name__=='__main__':main()
