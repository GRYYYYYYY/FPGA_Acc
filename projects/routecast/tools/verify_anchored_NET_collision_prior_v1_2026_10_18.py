"""Exhaustive weighted NET subset choices, independent of marginal formula."""
import hashlib,itertools,json,random
from collections import Counter
from fractions import Fraction
from pathlib import Path
from anchored_NET_collision_prior_v1 import marginal

def main():
 out=Path('experiments/anchored_NET_collision_prior_core_v1_2026-10-18');out.mkdir(exist_ok=False);rng=random.Random(9173);choices_checked=0
 for fixture in range(150):
  m=rng.randint(1,5);sets=[set(rng.sample(range(m),rng.randrange(m+1))) for _ in range(rng.randrange(4))];hist=Counter(map(len,sets))
  for weight in [Fraction(0),Fraction(1,2),Fraction(1)]:
   alternatives=[]
   for observed in sets:
    choices=list(itertools.combinations(range(m),len(observed)));probs={c:weight/len(choices) for c in choices};key=tuple(sorted(observed));probs[key]+=1-weight;alternatives.append(list(probs.items()))
   mean=[Fraction(0)]*m;empty=[Fraction(0)]*m;over=[Fraction(0)]*m
   for outcome in itertools.product(*alternatives):
    probability=Fraction(1);counts=Counter()
    for members,p in outcome:probability*=p;counts.update(members)
    for n in range(m):mean[n]+=probability*counts[n];empty[n]+=probability*(counts[n]==0);over[n]+=probability*max(0,counts[n]-1)
    choices_checked+=1
   for n in range(m):
    owners=Counter(len(s) for s in sets if n in s);actual=marginal(m,hist,owners,weight)
    assert actual==dict(expected_occupancy=mean[n],probability_empty=empty[n],expected_overflow=over[n])
   assert sum(mean)==sum(map(len,sets))
 invalid=[(0,{},{}),(2,{3:1},{}),(2,{1:1},{1:2}),(2,{0:1},{0:1}),(2,{2:1},{}),(2,{1:1},{2:1})]
 for args in invalid:
  try:marginal(*args)
  except ValueError:pass
  else:raise AssertionError(args)
 # Same group histogram, distinct observed overlap, different anchored risk.
 assert marginal(2,{1:2},{1:2})['expected_overflow']!=marginal(2,{1:2},{1:1})['expected_overflow']
 bindings={str(Path(p).resolve()):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in [__file__,'tools/anchored_NET_collision_prior_v1.py']}
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,random_set_fixtures=150,weights=['0','1/2','1'],weighted_NET_outcomes=choices_checked,invalid_fixtures=len(invalid),mass_conservation=True,scope='Exact declared mixture prior only, no source forecasts or target labels examined.'),f,indent=2)
 print(json.dumps(dict(status='pass',fixtures=150,weighted_outcomes=choices_checked)))
if __name__=='__main__':main()
