"""Independent original XML audit of every newly produced bank path and final state."""
import json
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'persistent_complete_chain_v1_2026-10-09';receipt=json.loads((D/'verification.json').read_text())
for p,h in receipt['bindings'].items():assert sha(p)==h
inv=None;rows=[]
for step in range(1,4):
 ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';meta=json.loads(ep.read_text());q={x['connection_id']:x for x in meta['connections']}
 budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads((E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json').read_text())}
 if inv is None:inv=read(meta['inputs']['graph']['path'],meta['graph_sha256'])
 data=json.loads((D/f'step_{step}_result.json').read_text());count=0
 def check(cid,path):
  assert path[0]==[q[cid]['source'],None] and path[-1][0]==q[cid]['sink'];assert len({n for n,s in path})==len(path)
  r,c=inv.classes[inv.node_classes[path[0][0]]];delay=r*c/2
  for (u,_),(v,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,s))==1;r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
  assert delay<=budgets[cid]
 for cid,options in data['bank'].items():
  for option in options:check(int(cid),option['path']);count+=1
 paths={int(cid):path for cid,path in data['paths'].items()};assert set(paths)==set(q)==set(budgets)
 owners=defaultdict(set);parents=defaultdict(set)
 for cid,path in paths.items():
  check(cid,path);net=q[cid]['net_id']
  for n,s in path:owners[n].add(net)
  for (u,_),(v,s) in zip(path,path[1:]):parents[net,v].add((u,s))
 assert all(len(ns)<=int(inv.physical.nodes[n][1]) for n,ns in owners.items()) and all(len(ps)==1 for ps in parents.values())
 rows.append(dict(step=step,bank_paths_checked=count,selected_connections=len(paths)))
out=D/'independent_paths_verification.json';assert not out.exists();out.write_text(json.dumps(dict(rows=rows,bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(Path(__file__))},scope='All fresh bank paths originalXML/Fraction budgets; complete selected-state uniqueNET capacity/sharedparent. Native/canonical and transaction publication not executed by this verifier.'),indent=2)+'\n');print(rows,flush=True)
