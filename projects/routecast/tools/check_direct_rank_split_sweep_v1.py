"""Independent full-field enumeration with actual distinct spatial scopes."""
import json,random
from fractions import Fraction as F
from pathlib import Path
from direct_rank_domain_v1 import BinaryDomain, training_objective
from direct_rank_objective_v1 import components
from direct_rank_split_sweep_v1 import scan
from exact_factor_elimination_v1 import sha

def make_domain(rng,n):
 ids=sorted(rng.sample(range(200),n));truth=[rng.randrange(2) for _ in ids];memberships=[[j for j in range(4) if rng.randrange(2)] for _ in ids];keys=[(j,) for j in range(4)];capacities=[rng.randint(1,10) for _ in keys];controls=[(F(0),F(1,2),F(0),F(1,2)),(F(1,4),F(1,3),F(-1,4),F(2,3))]
 return BinaryDomain(ids,truth,[1]*n,memberships,keys,capacities,max(1,n//3),2,controls)

def main():
 rng=random.Random(20261020);total=0
 for trial in range(120):
  domains=[(str(c),make_domain(rng,rng.randint(3,9))) for c in range(rng.randint(1,3))];fields=[[rng.randrange(2) for _ in d.ids] for _,d in domains];mapping=[(c,i) for c,(_,d) in enumerate(domains) for i in range(len(d.ids))];X=[[rng.randint(-2,3) for _ in range(3)] for _ in mapping];members=rng.sample(range(len(mapping)),rng.randint(1,len(mapping)));minimum=rng.randint(1,3);saved=[p.copy() for p in fields];got=scan(X,domains,fields,members,minimum,True);assert fields==saved;baseline=training_objective(domains,fields);reference=[]
  for f in range(3):
   for threshold in sorted(set(X[i][f] for i in members))[:-1]:
    left=[i for i in members if X[i][f]<=threshold];right=[i for i in members if X[i][f]>threshold]
    if min(len(left),len(right))<minimum:continue
    for a,b in [(0,0),(0,1),(1,0),(1,1)]:
     proposal=[p.copy() for p in fields]
     for i in left:
      c,j=mapping[i];proposal[c][j]=a
     for i in right:
      c,j=mapping[i];proposal[c][j]=b
     reference.append(((f,threshold,a,b),training_objective(domains,proposal)))
  assert got['trace']==reference and got['candidates']==len(reference) and got['before']==baseline
  eligible=[(v,key) for key,v in reference if v<baseline];expected=min(eligible) if eligible else (baseline,None);assert (got['after'],got['choice'])==expected;total+=len(reference)
 root=Path(__file__).resolve().parents[1];D=root/'experiments/direct_rank_split_sweep_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),root/'tools/direct_rank_split_sweep_v1.py',root/'tools/direct_rank_sparse_state_v1.py',root/'tools/direct_rank_domain_v1.py',root/'experiments/wbuart_direct_rank_sparse_contract_v1_2026-10-20/verification.json'];v={'status':'PASS_ALL_TINY_SPARSE_CANDIDATES_FULL_FIELD_REFERENCE','trials':120,'candidate_objectives':total,'bindings':{str(p):sha(p) for p in files},'scope':'Distinct spatial scopes and arbitrary subset/background states; sparse sweep qualification only, no real tree fit or speed claim.'};(D/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(v['status'],120,total)
if __name__=='__main__':main()
