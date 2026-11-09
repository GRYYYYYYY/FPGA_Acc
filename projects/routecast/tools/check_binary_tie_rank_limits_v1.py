"""Exhaust all strict score permutations and perfectly separated topK subsets."""
import json,itertools,math
from pathlib import Path
from binary_tie_rank_limits_v1 import limits
from prediction_metrics import spearman
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def main():
 permutations=0;separated=0
 for n in range(2,8):
  for positives in range(1,n):
   truth=[1]*positives+[0]*(n-positives);maximum=-1;minimum_hits=[n+1]*n;maximum_hits=[-1]*n
   for scores in itertools.permutations(range(n)):
    value=spearman(scores,truth);maximum=max(maximum,value);permutations+=1
    if min(scores[:positives])<=max(scores[positives:]):continue
    separated+=1;order=sorted(range(n),key=lambda i:(-scores[i],i))
    for k in range(1,n+1):
     hits=len(set(order[:k])&set(range(k)));minimum_hits[k-1]=min(minimum_hits[k-1],hits);maximum_hits[k-1]=max(maximum_hits[k-1],hits)
   for k in range(1,n+1):
    ref=limits(n,positives,k);assert abs(maximum-math.sqrt(ref['maximum_strict_score_spearman_squared']))<=1e-12;assert minimum_hits[k-1]==ref['perfect_separation_minimum_topK_hits'] and maximum_hits[k-1]==ref['perfect_separation_maximum_topK_hits']
   assert spearman(truth,truth)==1
 rejected=0
 for args in [(1,0,1),(4,0,1),(4,4,1),(4,2,0),(4,2,5),(True,1,1)]:
  try:limits(*args)
  except ValueError:rejected+=1
  else:raise AssertionError('invalid binary domain accepted')
 D=R/'experiments/binary_tie_rank_limits_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/binary_tie_rank_limits_v1.py',R/'tools/prediction_metrics.py'];(D/'verification.json').write_text(json.dumps({'status':'ALL_N2_TO7_STRICT_PERMUTATION_AND_TOPK_LIMITS_PASS','permutations':permutations,'perfect_separation_permutations':separated,'invalid_rejections':rejected,'bindings':{str(p):sha(p) for p in files},'scope':'Strict distinct score theorem only; score ties can change the bound. No original metric/gate change and no claim about actual forecast optimality.'},indent=2)+'\n');print('BINARY_TIE_LIMITS_PASS',permutations,separated)
if __name__=='__main__':main()
