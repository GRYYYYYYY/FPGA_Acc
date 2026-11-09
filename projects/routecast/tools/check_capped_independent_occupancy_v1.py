"""Independent exhaustive Bernoulli product reference, including clipping trap."""
import itertools,json,random
from pathlib import Path
from fractions import Fraction as F
from capped_independent_occupancy_v1 import moments
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def main():
 rng=random.Random(20261020);assignments=0
 for trial in range(500):
  n=rng.randrange(9);ps=[F(rng.randrange(7),6) for _ in range(n)];cap=rng.randrange(n+3);reference={key:F(0) for key in ['expected_demand','expected_capped_occupancy','expected_excess','probability_over_capacity']}
  for bits in itertools.product([0,1],repeat=n):
   probability=F(1)
   for p,bit in zip(ps,bits):probability*=p if bit else 1-p
   demand=sum(bits)
   for key,value in [('expected_demand',demand),('expected_capped_occupancy',min(cap,demand)),('expected_excess',max(0,demand-cap)),('probability_over_capacity',int(demand>cap))]:reference[key]+=probability*value
   assignments+=1
  assert moments(ps,cap)==reference
 fixture=moments([F(1,2),F(1,2)],1);assert fixture=={'expected_demand':F(1),'expected_capped_occupancy':F(3,4),'expected_excess':F(1,4),'probability_over_capacity':F(1,4)}
 rejected=0
 for ps,cap in [([0.5],1),([F(-1,2)],1),([F(3,2)],1),([True],1),([],True),([],-1),([],1.0)]:
  try:moments(ps,cap)
  except ValueError:rejected+=1
  else:raise AssertionError('invalid domain accepted')
 D=R/'experiments/capped_independent_occupancy_contract_v1_2026-10-20';D.mkdir(exist_ok=False);paths=[Path(__file__),R/'tools/capped_independent_occupancy_v1.py'];(D/'verification.json').write_text(json.dumps({'status':'ALL500_EXHAUSTIVE_BERNOULLI_PRODUCTS_AND_CLIPPING_TRAP_PASS','random_models':500,'exhaustive_assignments':assignments,'invalid_rejections':rejected,'bindings':{str(p):sha(p) for p in paths},'scope':'Exact independent inclusion distribution only. E[min(C,X)] differs from min(C,E[X]); neither conditions on joint route feasibility or proves forecast quality.'},indent=2)+'\n');print('CAPPED_OCCUPANCY_CONTRACT_PASS',assignments,rejected)
if __name__=='__main__':main()
