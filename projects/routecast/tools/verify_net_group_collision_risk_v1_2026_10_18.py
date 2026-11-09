"""Exact exhaustive independent Bernoulli and whole-NET group-choice oracles."""
import json,random,itertools,hashlib
from pathlib import Path
from fractions import Fraction
from collections import Counter
from net_group_collision_risk_v1 import independent_overflow,unit_group_expectation
R=Path(__file__).resolve().parents[1];out=R/'experiments/net_group_collision_risk_core_v1_2026-10-18';out.mkdir();rng=random.Random(20261018)
for trial in range(200):
 n=rng.randrange(7);ps=[Fraction(rng.randrange(5),4) for _ in range(n)];capacity=rng.randrange(6);oracle=Fraction(0)
 for bits in itertools.product([0,1],repeat=n):
  probability=Fraction(1)
  for bit,p in zip(bits,ps):probability*=p if bit else 1-p
  oracle+=probability*max(0,sum(bits)-capacity)
 assert independent_overflow(ps,capacity)==oracle
for trial in range(200):
 size=rng.randrange(1,5);ks=[rng.randrange(size+1) for _ in range(rng.randrange(5))]
 choices=[list(itertools.combinations(range(size),k)) for k in ks];outcomes=list(itertools.product(*choices));loads=[Fraction(0)]*size;empty=[Fraction(0)]*size;over=[Fraction(0)]*size
 for outcome in outcomes:
  occupancy=Counter(n for selected in outcome for n in selected)
  for n in range(size):loads[n]+=occupancy[n];empty[n]+=int(occupancy[n]==0);over[n]+=max(0,occupancy[n]-1)
 actual=unit_group_expectation(size,Counter(ks))
 for n in range(size):
  assert loads[n]/len(outcomes)==actual['expected_occupancy'] and empty[n]/len(outcomes)==actual['probability_empty'] and over[n]/len(outcomes)==actual['expected_overflow']
 assert actual['expected_overflow']==independent_overflow([Fraction(k,size) for k in ks],1)
assert unit_group_expectation(2,{2:1})['expected_overflow']==0
assert unit_group_expectation(2,{1:2})['expected_overflow']==Fraction(1,4)
negative=[lambda:independent_overflow([Fraction(3,2)],1),lambda:independent_overflow([.5],1),lambda:independent_overflow([1],-1),lambda:unit_group_expectation(0,{}),lambda:unit_group_expectation(2,{3:1}),lambda:unit_group_expectation(2,{1:-1})]
for call in negative:
 try:call()
 except ValueError:pass
 else:raise AssertionError('invalid prior admitted')
paths=[Path(__file__),R/'tools/net_group_collision_risk_v1.py']
with (out/'verification.json').open('x') as stream:json.dump(dict(status='pass',Bernoulli_exhaustive_fixtures=200,whole_NET_group_exhaustive_fixtures=200,shared_NET_not_independent_connections_fixture=True,negative_fixtures=len(negative),bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},scope='Exact expectation under declared independent uniform NET-choice model only; no native stochastic equivalence or prediction result.'),stream,indent=2)
print('COLLISION PRIOR400 EXHAUSTIVE FIXTURES PASS',flush=True)
