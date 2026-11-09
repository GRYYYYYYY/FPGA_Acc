"""Rational expected-demand score ordering and tie-capture reference checks."""
import pathlib,json,hashlib,random,itertools
from fractions import Fraction
from prospective_pressure_metrics_v1 import metrics
from prediction_metrics import spearman
R=pathlib.Path(__file__).resolve().parents[1]
def main():
 rng=random.Random(1019);checked=0
 for n in range(2,9):
  for repeat in range(20):
   scores=[Fraction(rng.randrange(4),rng.choice([2,3,7])) for _ in range(n)];truth=[rng.randrange(5) for _ in range(n)];truth[0]+=1;k=max(1,n//2);m=metrics(scores,truth,k,list(range(n)));rho=spearman(scores,truth);assert m['spearman'] is None if rho is None else abs(m['spearman']-rho)<1e-12
   boundary=sorted(scores,reverse=True)[k-1];above=[i for i,x in enumerate(scores) if x>boundary];equal=[i for i,x in enumerate(scores) if x==boundary];possible=[Fraction(sum(truth[i] for i in above)+sum(truth[i] for i in chosen),sum(truth)) for chosen in itertools.combinations(equal,k-len(above))];assert Fraction(m['capture'])==sum(possible)/len(possible);assert [Fraction(str(x)) for x in scores]==scores;checked+=1
 O=R/'experiments/mmc_full_NET_ensemble_fraction_metric_contract_v1_2026-10-19';O.mkdir();files=[pathlib.Path(__file__).resolve(),R/'tools/prospective_pressure_metrics_v1.py',R/'tools/prediction_metrics.py',R/'tools/verify_MMC_full_NET_ensemble_metrics_v1_2026_10_19.py'];proof=dict(status='140_rational_score_rank_and_exact_tie_enumeration_checks_pass',bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},checked_cases=checked,scope='Rational score metric contract only; complete model outputs and real metric audit still pending.')
 with (O/'verification.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
 print(proof['status'])
if __name__=='__main__':main()
