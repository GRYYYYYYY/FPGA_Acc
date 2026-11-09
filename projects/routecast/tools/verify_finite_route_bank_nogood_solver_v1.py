"""Exhaustive oracle and independently replayed ordinary proofs on small CSPs."""
import itertools,json,random
from pathlib import Path
from collections import defaultdict
from finite_route_bank_nogood_solver_v1 import solve
from native_resume_prototype.source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/finite_route_bank_nogood_solver_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
def valid(bank,q,cap,selection):
 owners=defaultdict(set);parents=defaultdict(dict)
 for c,i in selection.items():
  net=q[c]['net_id'];path=bank[c][i]['path']
  for n,s in path:owners[n].add(net)
  for (u,_),(n,s) in zip(path,path[1:]):
   if n in parents[net] and parents[net][n]!=(u,s):return False
   parents[net][n]=(u,s)
 return all(len(nets)<=cap[n] for n,nets in owners.items())
def replay(node,selected,bank,q,cap):
 selected=dict(selected)
 for c,i in node['forced']:
  assert c not in selected;legal=[j for j in range(len(bank[c])) if valid(bank,q,cap,{**selected,c:j})];assert legal==[i];selected[c]=i
 if node['kind']=='DEAD':
  c=node['empty_connection'];assert c not in selected and all(not valid(bank,q,cap,{**selected,c:j}) for j in range(len(bank[c])));return
 if node['kind']=='SOLUTION':assert len(selected)==len(bank) and valid(bank,q,cap,selected);return
 c=node['connection'];legal=[j for j in range(len(bank[c])) if valid(bank,q,cap,{**selected,c:j})];assert [child['index'] for child in node['children']]==legal
 for child in node['children']:replay(child['proof'],{**selected,c:child['index']},bank,q,cap)
rng=random.Random(7831);rows=[]
for trial in range(80):
 q={c:{'net_id':rng.randrange(3)} for c in range(4)};cap={n:(rng.randrange(1,4) if n<3 else 4) for n in range(20)};bank={c:[{'path':[[10+c,None],[rng.randrange(3),7],[15+c,8]]} for i in range(rng.randrange(1,4))] for c in q};feasible=any(valid(bank,q,cap,dict(zip(bank,indices))) for indices in itertools.product(*(range(len(bank[c])) for c in bank)));result=solve(bank,q,cap,100000);assert (result['status']=='FOUND')==feasible
 if feasible:assert valid(bank,q,cap,result['selection'])
 else:replay(result['proof'],{},bank,q,cap)
 rows.append(dict(case=trial,status=result['status'],learned_nogoods=result['learned_nogoods'],nogood_hits=result['nogood_hits']))
assert any(r['learned_nogoods'] for r in rows)
bindings=closure([Path(__file__),R/'tools/finite_route_bank_nogood_solver_v1.py']);assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,cases=80,rows=rows,scope='Exhaustive allassignments oracle with unique-NET capacity including capacities2/3 and sameNET parent conflicts; every UNSAT ordinary proof independently replayed. Small cases only, not real graph/timing coverage.'),indent=2)+'\n');print(dict(cases=80,feasible=sum(r['status']=='FOUND' for r in rows),unsat=sum(r['status']=='FINITE_BANK_EXHAUSTED' for r in rows)))
