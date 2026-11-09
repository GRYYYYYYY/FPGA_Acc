"""Finite weighted Bernoulli enumeration vs closed form; no route label use."""
import itertools,random,pathlib,json,hashlib
from fractions import Fraction
from independent_NET_overflow_expectation_v1 import unit_capacity
R=pathlib.Path(__file__).resolve().parents[1];rng=random.Random(1019);checked=states=0
for n in range(8):
 for repeat in range(40):
  ps=[Fraction(rng.randrange(5),4) for _ in range(n)];v=unit_capacity(ps);mass=Fraction(0);overflow=Fraction(0);probability=Fraction(0)
  for bits in itertools.product([0,1],repeat=n):
   weight=Fraction(1)
   for p,b in zip(ps,bits):weight*=p if b else 1-p
   count=sum(bits);mass+=weight;overflow+=weight*max(0,count-1);probability+=weight*int(count>1);states+=1
  assert mass==1 and v['expected_overflow']==overflow and v['probability_overflow']==probability;checked+=1
example=unit_capacity([Fraction(1,2),Fraction(1,2)]);assert example['mean_excess']==0 and example['expected_overflow']==Fraction(1,4)
for ps in [[-1],[2]]:
 try:unit_capacity(ps)
 except ValueError:pass
 else:raise AssertionError('bad marginal accepted')
O=R/'experiments/independent_NET_overflow_expectation_contract_v1_2026-10-19';O.mkdir();files=[pathlib.Path(__file__).resolve(),R/'tools/independent_NET_overflow_expectation_v1.py'];(O/'verification.json').write_text(json.dumps(dict(status='320_WEIGHTED_BERNOULLI_ENUMERATIONS_MATCH_EXPECTED_OVERFLOW_AND_COLLISION',bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},fixtures=checked,weighted_states=states,half_half_example={k:str(v) for k,v in example.items()},new_native_jobs=0,scope='Mathematical independent-NET prior only. E[(D-1)+] differs from(E[D]-1)+; no claim native occupancies follow independent Bernoulli model or that replacing the tested surcharge improves any outcome. Native/final-occupancy failures remain unchanged.'),indent=2)+'\n');print('PASS',checked,states,'half/half mean_excess0 expected_overflow1/4; no policy run')
