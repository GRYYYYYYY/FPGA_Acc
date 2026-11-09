"""Independent all-bank original XML audit, structural CNF check and naive RUP."""
import json
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from independent_route_cnf_structure_v1 import verify_encoding
from verify_certified_cnf_dependency_cdcl_v1 import verify
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'paired_history_chain_v1_arm0_step2_stage_1_2026-10-09'
receipt=json.loads((D/'verification.json').read_text())
for p,h in receipt['bindings'].items():assert sha(p)==h,p
p=D/'result.json';data=json.loads(p.read_text());bank={int(cid):opts for cid,opts in data['bank'].items()}
g=R/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits/rr_graph.xml';inv=read(g,sha(g))
q={row['connection_id']:row for row in json.loads((E/'adder_tree_2L032_move_sequence_2026-10-06/step_2_endpoints.json').read_text())['connections']}
budgets={row['connection_id']:F(*row['exact_delay_s']) for row in json.loads((E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_2_budgets.json').read_text())}
def check(cid,path):
 assert path[0]==[q[cid]['source'],None] and path[-1][0]==q[cid]['sink']
 assert len({n for n,s in path})==len(path)
 r,c=inv.classes[inv.node_classes[path[0][0]]];delay=r*c/2
 for (u,_),(v,s) in zip(path,path[1:]):
  assert inv.arc_multiplicities.get((u,v,s))==1
  r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
 assert delay<=budgets[cid]
assert set(bank)==set(q)
for cid,options in bank.items():
 for option in options:check(cid,option['path'])
verify_encoding(data['encoding'],bank,q,inv);verify(data['encoding']['clauses'],data['result'])
assert receipt['status']==data['result']['status']
if data['paths'] is not None:
 paths={int(cid):path for cid,path in data['paths'].items()};assert set(paths)==set(q)
 owners=defaultdict(set);parents=defaultdict(set)
 for cid,path in paths.items():
  check(cid,path);net=q[cid]['net_id']
  selected=[option['path'] for i,option in enumerate(bank[cid]) if data['result']['model'][str(data['encoding']['path_vars'][f'{cid}:{i}'])]]
  assert selected==[path]
  for n,s in path:owners[n].add(net)
  for (u,_),(v,s) in zip(path,path[1:]):parents[net,v].add((u,s))
 assert all(len(ns)<=int(inv.physical.nodes[n][1]) for n,ns in owners.items())
 assert all(len(ps)==1 for ps in parents.values())
else:assert data['result']['status']!='SAT'
report=dict(status=receipt['status'],candidates=sum(map(len,bank.values())),rup_additions=len(data['result']['rup_additions']),full_selection=data['paths'] is not None,bindings={str(p):sha(p),str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(Path(__file__))},scope='Independent all bank XML/Fraction, exact structural encoding, naive RUP/model and full selection capacity/parent. Finite-bank feasibility only, not native or independent timing target acceptance.')
out=D/'independent_verification.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='bindings'},flush=True)
