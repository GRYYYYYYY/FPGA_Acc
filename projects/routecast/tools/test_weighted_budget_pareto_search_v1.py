"""Exact simple-tail enumeration oracle including c0/c1, zero cycles and frozen seeds."""
import json,random,hashlib,copy
from pathlib import Path
from fractions import Fraction as F
from weighted_budget_pareto_search_v1 import search
from reverse_raw_delay_bounds_v1 import ReverseBounds
R=Path(__file__).resolve().parents[1];D=R/'experiments/weighted_budget_pareto_contract_v1_2026-10-19'
def build(n,edges):
 offsets=[0];dest=[];raw=[]
 for u in range(n):
  for a,b,w in sorted(edges):
   if a==u:dest.append(b);raw.append(w)
  offsets.append(len(dest))
 return offsets,dest,raw

def enumerate_paths(offsets,dest,raw,caps,initial,target,c,prices,budget):
 own=set(initial);p,q=c.numerator,c.denominator;answers=[]
 def dfs(u,delay,cost,visited,path,join):
  if u==target:
   if delay<=budget:answers.append((cost,delay,join,tuple(path)))
   return
  for e in range(offsets[u],offsets[u+1]):
   v=dest[e]
   if v in own or v in visited or caps[v]<=0:continue
   nd=delay+raw[e]
   if nd>budget:continue
   dfs(v,nd,cost+p*raw[e]+(q-p)*prices.get(v,0),visited|{v},path+[e],join)
 for node,delay in initial.items():dfs(node,delay,p*delay,{node},[],node)
 return answers

def main():
 D.mkdir(exist_ok=False);rng=random.Random(20261019);feasible=none=paths=unknown=small_exhausted=0;coefficients=[F(0),F(1,4),F(1,2),F(3,4),F(1)]
 for trial in range(200):
  n=rng.randrange(4,7);edges=[(u,v,rng.randrange(5)) for u in range(n) for v in range(n) if u!=v and rng.random()<.32];frozen=trial%2==0
  if frozen:edges=[x for x in edges if x[:2]!=(0,1)]+[(0,1,1)]
  offsets,dest,raw=build(n,edges);initial={0:0,1:1} if frozen else {0:0};caps=[1]*n
  if trial%7==0 and n>4:caps[2]=0
  c=coefficients[trial%len(coefficients)];prices={i:rng.randrange(11) for i in range(n)};budget=rng.randrange(1,11);bound=ReverseBounds(offsets,dest,raw).bound(n-1,budget);expected=enumerate_paths(offsets,dest,raw,caps,initial,n-1,c,prices,budget);paths+=len(expected);before=copy.deepcopy([offsets,dest,raw,caps,initial,prices]);result=search(offsets,dest,raw,caps,initial,n-1,c,prices,budget,bound)
  if expected:
   feasible+=1;assert result['status']=='FOUND' and result['objective_numerator']==min(a[0] for a in expected);assert (result['objective_numerator'],result['raw'],result['join'],result['path_slots']) in expected
  else:none+=1;assert result['status']=='NO_BUDGET_PATH_FOR_FIXED_TREE'
  assert [offsets,dest,raw,caps,initial,prices]==before
  limited=search(offsets,dest,raw,caps,initial,n-1,c,prices,budget,bound,max_labels=1)
  if limited['status']=='UNKNOWN_LABEL_LIMIT':unknown+=1;assert limited['labels_created']==1
  elif limited['status']=='NO_BUDGET_PATH_FOR_FIXED_TREE':small_exhausted+=1;assert not expected
  else:raise AssertionError('nonseed target cannot be found with one label')
  assert [offsets,dest,raw,caps,initial,prices]==before
 offsets,dest,raw=build(4,[(0,1,1),(1,3,1),(0,2,3),(2,3,2)]);prices={1:100};c=F(1,2);bound=ReverseBounds(offsets,dest,raw).bound(3,2);r=search(offsets,dest,raw,[1]*4,{0:0},3,c,prices,2,bound);assert r['status']=='FOUND' and r['raw']==2 and r['objective_numerator']==102
 files=[Path(__file__).resolve(),R/'tools/weighted_budget_pareto_search_v1.py',R/'tools/reverse_raw_delay_bounds_v1.py'];(D/'verification.json').write_text(json.dumps(dict(status='ALL200_WEIGHTED_BUDGET_SEARCHES_MATCH_EXHAUSTIVE_SIMPLE_TAILS',random_graphs=200,feasible=feasible,no_budget_fixed_tree=none,enumerated_feasible_paths=paths,small_cap_UNKNOWN=unknown,small_cap_exhausted_no_path=small_exhausted,input_unchanged=True,c0_and_c1_tested=True,weighted_overbudget_counterexample_pass=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Search kernel only. Relaxed raw bounds feasibility pruning, objective bound p*h_raw. Frozen-tree no-path not wholeNET/global impossibility. No real predictor quality/compiled timing claim.'),indent=2)+'\n');print(feasible,none,paths,unknown,small_exhausted)
if __name__=='__main__':main()
