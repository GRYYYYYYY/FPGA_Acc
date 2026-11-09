"""Check every path-choice projection of small encodings using an independent SAT evaluator."""
import json,itertools,random
from collections import defaultdict
from pathlib import Path
from finite_route_bank_cnf_v1 import encode
from native_resume_prototype.source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/finite_route_bank_cnf_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
def sat(clauses,values):
 values=dict(values)
 while True:
  pending=[];unit=None
  for clause in clauses:
   if any(abs(x) in values and values[abs(x)]==(x>0) for x in clause):continue
   residual=[x for x in clause if abs(x) not in values]
   if not residual:return False
   pending.append(residual)
   if len(residual)==1:unit=residual[0]
  if not pending:return True
  if unit is None:break
  values[abs(unit)]=unit>0
 x=abs(pending[0][0]);return sat(pending,{**values,x:True}) or sat(pending,{**values,x:False})
def legal(bank,q,cap,choice):
 owners=defaultdict(set);parents=defaultdict(dict)
 for cid,index in choice.items():
  net=q[cid]['net_id'];path=bank[cid][index]['path']
  for n,s in path:owners[n].add(net)
  for (u,_),(n,s) in zip(path,path[1:]):
   if n in parents[net] and parents[net][n]!=(u,s):return False
   parents[net][n]=(u,s)
 return all(len(nets)<=cap[n] for n,nets in owners.items())
rng=random.Random(9041);projections=0
for case in range(40):
 q={c:{'net_id':c if case%2 else rng.randrange(2)} for c in range(3)};cap={n:3 for n in range(20)};cap[0]=case%3+1;cap[1]=(case+1)%3+1;bank={c:[{'path':[[10+c,None],[rng.randrange(2),7],[15+c,8]]} for i in range(2)] for c in q};cnf=encode(bank,q,cap)
 for indices in itertools.product(range(2),repeat=3):
  choices=dict(enumerate(indices));values={var:choices[int(key.split(':')[0])]==int(key.split(':')[1]) for key,var in cnf['path_vars'].items()};assert sat(cnf['clauses'],values)==legal(bank,q,cap,choices);projections+=1
bindings=closure([Path(__file__),R/'tools/finite_route_bank_cnf_v1.py']);assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,cases=40,path_choice_projections=projections,scope='Every fixed path-choice assignment compared to independent uniqueNET capacity/sameNET parent oracle via independent small SAT extension evaluator. Capacities1/2/3, no claim real154 component solved.'),indent=2)+'\n');print(dict(cases=40,path_choice_projections=projections))
