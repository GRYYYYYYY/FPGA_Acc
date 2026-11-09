"""Independent pair-count ranks and componentwise training objective oracle."""
import json,random
from fractions import Fraction as F
from pathlib import Path
from direct_rank_objective_v1 import components,objective
from prediction_metrics import compare
from exact_factor_elimination_v1 import sha

def reference(a,b,k):
 keys=list(a)
 def ranks(v):return {key:F(sum(v[x]<v[key] for x in keys))+F(sum(v[x]==v[key] for x in keys)-1,2) for key in keys}
 x,y=ranks(a),ranks(b);center=F(len(keys)-1,2);cross=sum((x[t]-center)*(y[t]-center) for t in keys);va=sum((x[t]-center)**2 for t in keys);vb=sum((y[t]-center)**2 for t in keys);rank=cross*abs(cross)/(va*vb) if va*vb else F(-2)
 # Membership determined by individual score+ID comparisons, no sorted slicing.
 def top(v):return {t for t in keys if sum(v[q]>v[t] or (v[q]==v[t] and q<t) for q in keys)<k}
 return rank,F(len(top(a)&top(b)),k)

def main():
 rng=random.Random(20261020);fields=[];checks=0
 for trial in range(600):
  n=rng.randint(1,25);keys=rng.sample(range(100),n);a={key:F(rng.randint(-3,3),rng.randint(1,4)) for key in keys};b={key:rng.randrange(3) for key in reversed(keys)};k=rng.randint(1,n);actual=components(a,b,k);assert actual==reference(a,b,k)
  perm=list(a.items());rng.shuffle(perm);assert components(dict(perm),b,k)==actual
  legacy=compare(a,b,k);rho=legacy['spearman'];assert (rho is None and actual[0]==-2) or rho is not None and abs(float(actual[0])-rho*abs(rho))<=1e-12
  assert abs(float(actual[1])-legacy['precision_at_k'])<=1e-15;fields.append(actual);checks+=1
 for trial in range(400):
  cases=[]
  for _ in range(rng.randint(1,6)):
   vectors=[(*rng.choice(fields),*rng.choice(fields)) for _ in range(3)];cases.append({'candidate':vectors[0],'controls':vectors[1:]})
  failed=negative=0;deficit=total=F(0)
  for case in cases:
   for baseline in case['controls']:
    improve=False;nonreg=True
    for i in range(4):
     d=case['candidate'][i]-baseline[i];total+=d
     if d<0:negative+=1;deficit-=d;nonreg=False
     if d>0:improve=True
     if i in (0,2) and (case['candidate'][i]==-2 or baseline[i]==-2):nonreg=False
    failed+=not(nonreg and improve)
  assert objective(cases)==(failed,negative,deficit,-total)
 root=Path(__file__).resolve().parents[1];out=root/'experiments/direct_rank_objective_contract_v1_2026-10-20';out.mkdir(exist_ok=False);files=[Path(__file__),root/'tools/direct_rank_objective_v1.py',root/'tools/prediction_metrics.py',root/'experiments/wbuart_direct_rank_partition_design_v1_2026-10-20/protocol.json'];v={'status':'PASS_EXACT_RANK_TOPK_AND_TRAIN_OBJECTIVE_KERNEL','rank_fields':checks,'objective_trials':400,'permutation_checks':600,'bindings':{str(p):sha(p) for p in files},'scope':'Kernel only; no tree trainer, real fit, heldout gain or novelty claim.'};(out/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(v['status'],checks,400)
if __name__=='__main__':main()
