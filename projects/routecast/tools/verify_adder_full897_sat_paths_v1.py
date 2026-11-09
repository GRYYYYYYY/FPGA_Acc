"""Map actual SAT model to516 physical paths and independently audit whole selection."""
import json
from pathlib import Path
from collections import defaultdict
from fractions import Fraction as F
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_full897_sat_paths_verification_v1_2026-10-09'
reports=[E/'adder_full897_cnf_structure_verification_v1_2026-10-09/verification.json',E/'adder_full897_cnf_solve_verification_v1_2026-10-09/verification.json'];bindings=closure([Path(__file__)])
for p in reports:
 r=json.loads(p.read_text());assert all(sha(f)==h for f,h in r['bindings'].items())
 for f,h in r['bindings'].items():
  if f in bindings:assert bindings[f]==h
  bindings[f]=h
 bindings[str(p)]=sha(p)
assert r['status']=='SAT' and r['certificate_replay_pass'];D.mkdir(exist_ok=False)
cp=E/'adder_full897_cnf_v1_2026-10-09/encoding.json';rp=E/'adder_full897_cnf_solve_v1_2026-10-09/result.json';cnf=json.loads(cp.read_text());result=json.loads(rp.read_text());assert result['status']=='SAT';model={int(k):v for k,v in result['model'].items()};assert set(model)==set(range(1,len(cnf['variables'])+1));assert all(any(model[abs(x)]==(x>0) for x in c) for c in cnf['clauses'])
bp=E/'adder_local_capacity_detours_v7_2026-10-09/step_3.json';bank={int(c):p for c,p in json.loads(bp.read_text())['bank'].items()};mp=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(mp.read_text());q={x['connection_id']:x for x in meta['connections']};budgetp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_3_budgets.json';budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(budgetp.read_text())};inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);selection={};owners=defaultdict(set);parents=defaultdict(dict);paths={}
for cid,options in bank.items():
 chosen=[i for i in range(len(options)) if model[cnf['path_vars'][f'{cid}:{i}']]];assert len(chosen)==1;index=chosen[0];selection[cid]=index;option=options[index];path=option['path'];paths[cid]=path;query=q[cid];net=query['net_id'];assert path[0]==[query['source'],None] and path[-1][0]==query['sink'];assert len({n for n,s in path})==len(path);r,c=inv.classes[inv.node_classes[query['source']]];delay=r*c/2
 for n,s in path:owners[n].add(net)
 for (u,_),(v,s) in zip(path,path[1:]):
  assert inv.arc_multiplicities.get((u,v,s))==1;nr,nc=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+nr/2)*nc+td
  assert v not in parents[net] or parents[net][v]==(u,s);parents[net][v]=(u,s)
 assert delay==F(*option['exact_delay_s']) and delay<=budgets[cid]
assert set(selection)==set(q) and len(selection)==516;assert all(len(nets)<=int(inv.physical.nodes[n][1]) for n,nets in owners.items());p=D/'selection.json';p.write_text(json.dumps(dict(selection=selection,paths=paths),indent=2)+'\n')
for p in (p,cp,rp,bp,mp,budgetp):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,status='ALL516_PHYSICAL_MODEL_BUDGET_CAPACITY_PARENT_PASS',connections=516,scope='Full selected paths verified; native/canonical STA, retained routes and matched cost still required. Budgets are positive-control target-derived, not independent timing specification.'),indent=2)+'\n');print('ALL516_PHYSICAL_MODEL_BUDGET_CAPACITY_PARENT_PASS')
