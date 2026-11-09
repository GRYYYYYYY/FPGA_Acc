"""Exhaustive finite selections and rational convex mixture rank-bound checks."""
import json,hashlib,random,itertools
from fractions import Fraction as F
from pathlib import Path
from spatial_candidate_rank_bounds_v1 import rank_bounds
R=Path(__file__).resolve().parents[1];D=R/'experiments/spatial_candidate_rank_bounds_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def top(values,caps,k):return set(sorted(range(len(caps)),key=lambda i:(-F(values[i],caps[i]),i))[:k])
def main():
 D.mkdir(exist_ok=False);rng=random.Random(40720261020);points=0;mixtures=0
 for _ in range(250):
  n=rng.randrange(2,9);k=rng.randrange(1,n+1);caps=[rng.randrange(1,7) for _ in range(n)];pools=[[[rng.randrange(6) for _ in range(n)] for _ in range(rng.randrange(1,4))] for _ in range(rng.randrange(1,5))];lower=[sum(min(p[i] for p in pool) for pool in pools) for i in range(n)];upper=[sum(max(p[i] for p in pool) for pool in pools) for i in range(n)];bounds=rank_bounds(lower,upper,caps,k);excluded={i for i,r in enumerate(bounds) if r['excluded_from_topK']};guaranteed={i for i,r in enumerate(bounds) if r['guaranteed_in_topK']}
  def check(values):
   selected=top(values,caps,k);assert not excluded&selected and guaranteed<=selected
   order=sorted(range(n),key=lambda i:(-F(values[i],caps[i]),i));ranks={i:j+1 for j,i in enumerate(order)}
   for i,b in enumerate(bounds):assert b['best_rank_lower_bound']<=ranks[i]<=b['worst_rank_upper_bound']
  for choice in itertools.product(*pools):check([sum(p[i] for p in choice) for i in range(n)]);points+=1
  for j in range(12):
   values=[F(0)]*n
   for pool in pools:
    weights=[rng.randrange(1,9) for _ in pool];total=sum(weights)
    for p,w in zip(pool,weights):
     for i in range(n):values[i]+=F(w,total)*p[i]
   check(values);mixtures+=1
  exact=[rng.randrange(9) for _ in range(n)];b=rank_bounds(exact,exact,caps,k);selected=top(exact,caps,k);assert {i for i,r in enumerate(b) if r['guaranteed_in_topK']}==selected and {i for i,r in enumerate(b) if not r['excluded_from_topK']}==selected
 # Independent intervals can be optimistic: target2 never wins in any convex mix here.
 b=rank_bounds([0,0,1],[2,2,1],[1]*3,1);assert not b[2]['excluded_from_topK']
 for a in range(101):assert 2 not in top([F(2*a,100),F(2*(100-a),100),F(1)],[1]*3,1)
 rejected=0
 for args in [([],[],[],1),([1],[0],[1],1),([0],[0],[0],1),([-1],[0],[1],1),([0],[1],[1],0)]:
  try:rank_bounds(*args)
  except ValueError:rejected+=1
  else:raise AssertionError('invalid bound admitted')
 files=[Path(__file__),R/'tools/spatial_candidate_rank_bounds_v1.py'];(D/'verification.json').write_text(json.dumps({'status':'ALL250_EXHAUSTIVE_POOL_POINT_AND3000_RATIONAL_MIXTURE_RANK_BOUNDS_PASS','point_selections':points,'rational_mixtures':mixtures,'degenerate_exact_rank_fixtures':250,'invalid_rejections':rejected,'optimistic_not_sufficient_fixture':True,'bindings':{str(p):sha(p) for p in files},'scope':'Necessary exclusion and sufficient guaranteed membership only under per-bin interval containment; possible membership does not imply joint feasibility.'},indent=2)+'\n');print('RANK_BOUND_CONTRACT_PASS',points,mixtures,rejected)
if __name__=='__main__':main()
