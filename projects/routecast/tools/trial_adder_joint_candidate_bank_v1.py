"""Finite original/current path bank with exact independent required-node bounds."""
import json
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_joint_candidate_bank_v1_2026-10-09';D.mkdir(exist_ok=False)
ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';m=json.loads(ep0.read_text());inv=read(m['inputs']['graph']['path'],m['graph_sha256']);edges={eid:arc for arc,eid in inv.physical.arcs.items()};bindings={str(Path(__file__)):sha(__file__),str(ep0):sha(ep0),m['inputs']['graph']['path']:m['graph_sha256']};rows=[]
def check(q,path,budget):
 assert path[0]==[q['source'],None] and path[-1][0]==q['sink'] and len({n for n,s in path})==len(path)
 rr,cc=inv.classes[inv.node_classes[q['source']]];delay=rr*cc/2
 for (u,_),(v,s) in zip(path,path[1:]):
  assert inv.arc_multiplicities.get((u,v,s))==1 and int(inv.physical.nodes[v][1])>0
  rr,cc=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+rr/2)*cc+td
 return delay,delay<=budget
for step in range(4):
 ep=ep0 if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';statepath=E/f'adder_reverse_live_owner_v1_2026-10-08/step_{step}.json';budgetpath=E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json';predpath=E/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json' if step==0 else E/f'adder_tree_2L032_move_sequence_audit_2026-10-06/step_{step}_prediction.json'
 queries={q['connection_id']:q for q in json.loads(ep.read_text())['connections']};state=json.loads(statepath.read_text())['state'];budgets={b['connection_id']:F(*b['exact_delay_s']) for b in json.loads(budgetpath.read_text())};pred={p['connection_id']:p for p in json.loads(predpath.read_text())['connections']};bank={};necessary=defaultdict(set);empty=[]
 for cid,q in queries.items():
  candidates=[];path=[[q['source'],None]];node=q['source']
  for eid in pred[cid]['physical_edge_ids']:
   u,v,s=edges[eid];assert u==node;path.append([v,s]);node=v
  for label,p in [('current',state[str(cid)]),('prediction',path)]:
   delay,passed=check(q,p,budgets[cid])
   if passed and not any(c['path']==p for c in candidates):candidates.append(dict(origin=label,path=p,delay_seconds=str(delay)))
  bank[str(cid)]=candidates
  if not candidates:empty.append(cid);continue
  required=set.intersection(*[{n for n,s in c['path']} for c in candidates])
  for n in required:necessary[n].add(q['net_id'])
 conflicts=[dict(node=n,capacity=int(inv.physical.nodes[n][1]),required_net_ids=sorted(nets)) for n,nets in sorted(necessary.items()) if len(nets)>int(inv.physical.nodes[n][1])]
 out=D/f'step_{step}.json';out.write_text(json.dumps(dict(bank=bank,empty_connection_ids=empty,required_node_capacity_conflicts=conflicts),indent=2)+'\n')
 for p in (ep,statepath,budgetpath,predpath,out):bindings[str(p)]=sha(p)
 row=dict(step=step,connections=len(bank),eligible_candidates=sum(map(len,bank.values())),empty_connections=len(empty),required_capacity_conflicts=len(conflicts),finite_bank_infeasible=bool(empty or conflicts));rows.append(row);print(row)
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Exact independent physical/Fraction audit of all current/prediction paths. Necessary-node capacity conflicts prove only this finite two-origin bank infeasible; do not prove original joint routing infeasible. No candidate installed.'),indent=2)+'\n')
