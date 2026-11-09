"""Trace RUP unit reasons; retain the original clauses supporting final empty clause."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_full861_rup_core_v1_2026-10-09';D.mkdir(exist_ok=False);vp=E/'adder_full861_cnf_unsat_binding_v1_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());ep=E/'adder_full861_cnf_v1_2026-10-09/encoding.json';rp=E/'adder_full861_cnf_solve_v1_2026-10-09/result.json';cnf=json.loads(ep.read_text());result=json.loads(rp.read_text());database=list(cnf['clauses']);base=len(database);graph={}
for added in result['rup_additions']:
 values={abs(x):x<0 for x in added};reasons={abs(x):set() for x in added};support=None
 while support is None:
  changed=False
  for index,clause in enumerate(database):
   if any(abs(x) in values and values[abs(x)]==(x>0) for x in clause):continue
   residual=set(x for x in clause if abs(x) not in values)
   deps={index}.union(*(reasons[abs(x)] for x in clause if abs(x) in values))
   if not residual:support=deps;break
   if len(residual)==1:
    x=next(iter(residual));values[abs(x)]=x>0;reasons[abs(x)]=deps;changed=True
  assert support is not None or changed
 graph[len(database)]=sorted(support);database.append(added)
assert database[-1]==[];needed=set();queue=[len(database)-1]
while queue:
 i=queue.pop()
 if i in needed:continue
 needed.add(i)
 if i>=base:queue.extend(graph[i])
original=sorted(i for i in needed if i<base);additions=sorted(i for i in needed if i>=base);roles={}
for index in original:
 for lit in database[index]:roles[abs(lit)]=cnf['variables'][abs(lit)-1]
core=dict(original_clause_indices=original,learned_addition_indices=[i-base for i in additions],original_clauses=[database[i] for i in original],rup_additions=[database[i] for i in additions],roles={str(i):r for i,r in sorted(roles.items())},reason_graph={str(i):r for i,r in graph.items()},scope='Proof-support core only; not minimal or irreducible; fixed finite candidate bank only.')
p=D/'core.json';p.write_text(json.dumps(core,indent=2)+'\n');bindings[str(p)]=sha(p)
for p in (ep,rp):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,original_clauses=len(original),learned_additions=len(additions),role_counts=dict(Counter(r['kind'] for r in roles.values())),scope=core['scope']);(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
