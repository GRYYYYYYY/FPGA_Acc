"""Exhaust all group decisions and score orders, independent pairwise ROC count."""
import json,itertools,random
from fractions import Fraction as F
from pathlib import Path
from feature_alias_bounds_v1 import limits
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def main():
 rng=random.Random(20261020);decisions=0;orders=0
 for trial in range(200):
  groups=[]
  for _ in range(rng.randrange(1,7)):
   n=rng.randrange(1,6);groups.append((n,rng.randrange(n+1)))
  result=limits(groups);errors=[]
  for assignment in itertools.product([0,1],repeat=len(groups)):
   errors.append(sum(p if not choice else n-p for (n,p),choice in zip(groups,assignment)));decisions+=1
  assert min(errors)==result['minimum_binary_errors']
  P=sum(p for n,p in groups);N=sum(n-p for n,p in groups);best=None
  for permutation in itertools.permutations(range(len(groups))):
   twice=sum(p*(n2-p2)*(2 if permutation[i]>permutation[j] else 1 if permutation[i]==permutation[j] else 0) for i,(n,p) in enumerate(groups) for j,(n2,p2) in enumerate(groups));value=F(twice,2*P*N) if P*N else None;best=max(best,value) if best is not None and value is not None else value;orders+=1
  assert result['maximum_ROC_AUC']==best
  assert sum(p if not choice else n-p for (n,p),choice in zip(groups,result['majority_decisions']))==min(errors)
 invalid=0
 for groups in [[],[(0,0)],[(2,3)],[(2,-1)],[(True,1)],[(2,.5)]]:
  try:limits(groups)
  except ValueError:invalid+=1
  else:raise AssertionError('invalid group accepted')
 D=R/'experiments/feature_alias_bounds_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/feature_alias_bounds_v1.py'];(D/'verification.json').write_text(json.dumps({'status':'ALL200_EXHAUSTIVE_GROUP_DECISIONS_AND_SCORE_ORDERS_PASS','binary_decisions':decisions,'strict_group_orders':orders,'invalid_rejections':invalid,'bindings':{str(p):sha(p) for p in files},'scope':'Limits for pointwise functions of fixed equal-feature groups only; not arbitrary graph/global models, original ranking gates or unseen performance.'},indent=2)+'\n');print('FEATURE_ALIAS_CONTRACT_PASS',decisions,orders)
if __name__=='__main__':main()
