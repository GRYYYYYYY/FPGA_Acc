"""Posthoc signal-support diagnosis; not tuning, new predictor, or changed gate."""
import pathlib,json,hashlib
from fractions import Fraction
from collections import Counter
from prefix_value_capture_bound_v1 import ceiling
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def probabilities(scores,k):
 counts=Counter(scores);left=k;prob={}
 for score,n in sorted(counts.items(),reverse=True):
  take=min(left,n);prob[score]=Fraction(take,n);left-=take
 assert not left and sum(prob[s]*n for s,n in counts.items())==k
 return prob
def main():
 E=R/'experiments/mmc_prospective_pressure_evaluation_v2_2026-10-19';rp=E/'results.json';vp=E/'independent_metric_verification_v1.json';result=json.loads(rp.read_text());verify=json.loads(vp.read_text());assert verify['status']=='all3_forecast_metrics_and_registered_decisions_independently_verified' and not result['all3_primary_gate_pass'];assert verify['bindings'][str(rp)]==sha(rp)
 O=R/'experiments/mmc_forward_forecast_signal_support_v1_2026-10-19';O.mkdir();domain=json.loads((E/'domain.json').read_text());k=len(domain)//20;bindings={str(p):sha(p) for p in [rp,vp,E/'domain.json',pathlib.Path(__file__).resolve(),R/'tools/prefix_value_capture_bound_v1.py']};rows=[]
 for row in result['episodes']:
  name=row['episode'];pp=E/(name+'_predictions.json');assert result['bindings'][str(pp)]==sha(pp);pred=json.loads(pp.read_text());tp=R/'experiments/mmc_prospective_pressure_targets_v2_2026-10-19'/name/'targets.json';assert result['bindings'][str(tp)]==sha(tp);target=json.loads(tp.read_text());truth={int(n):v for n,v in target['targets']['sum_checkpoint_overflow_units'].items()};t=[truth.get(n,0) for n in domain];total=sum(t);old=pred['previous_native'];warm=pred['native_retained'];changed=[i for i,(a,b) in enumerate(zip(old,warm)) if a!=b];assert len(old)==len(warm)==len(t)==258720
  po,pw=probabilities(old,k),probabilities(warm,k);count=Counter(zip(old,warm));mass=Counter()
  for a,b,v in zip(old,warm,t):mass[a,b]+=v
  changed_contribution=sum((pw[b]-po[a])*mass[a,b] for a,b in count if a!=b)/total;unchanged_contribution=sum((pw[b]-po[a])*mass[a,b] for a,b in count if a==b)/total;expected=Fraction(row['metrics']['sum_checkpoint_overflow_units']['native_retained']['capture'])-Fraction(row['metrics']['sum_checkpoint_overflow_units']['previous_native']['capture']);assert changed_contribution+unchanged_contribution==expected
  pairs=sorted(count);encoding={pair:i for i,pair in enumerate(pairs)};encoded=[encoding[a,b] for a,b in zip(old,warm)];bound=ceiling(encoded,t,k);assert bound['capture']>=Fraction(row['metrics']['sum_checkpoint_overflow_units']['native_retained']['capture']);groups=[dict(source_score=a,warm_score=b,nodes=count[a,b],future_pressure_mass=mass[a,b]) for a,b in pairs]
  rows.append(dict(episode=name,domain_nodes=len(domain),changed_score_nodes=len(changed),changed_score_domain_fraction=str(Fraction(len(changed),len(domain))),future_pressure_mass_on_changed_score_nodes=sum(t[i] for i in changed),future_pressure_mass_total=total,future_pressure_fraction_on_changed_score_nodes=str(Fraction(sum(t[i] for i in changed),total)),capture_delta_from_changed_score_nodes=str(changed_contribution),capture_delta_from_unchanged_score_nodes_via_tie_reallocation=str(unchanged_contribution),capture_delta_total=str(expected),groups=groups,pair_value_oracle_capture_ceiling=str(bound['capture'])))
  bindings[str(pp)]=sha(pp);bindings[str(tp)]=sha(tp);print(name,len(changed),float(Fraction(sum(t[i] for i in changed),total)),float(bound['capture']),flush=True)
 with (O/'review.json').open('x') as f:json.dump(dict(status='three_closed_forward_cases_signal_support_decomposed_exactly',bindings=bindings,episodes=rows,primary_gate_still_failed=True,new_native_jobs=0,new_predictor=False,scope='Posthoc diagnostic only. Oracle uses future labels to upper-bound functions of the perRR pair(source occupancy,warm demand), with uniform score-boundary ties; not a usable forecast or bound on spatial/graph/ID/context models. Source/warm changed support is not the full routing perturbation region. Unchanged scores can change selection probabilities through global tie sizes. No secondary target promotion, case replacement or timing claim.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
