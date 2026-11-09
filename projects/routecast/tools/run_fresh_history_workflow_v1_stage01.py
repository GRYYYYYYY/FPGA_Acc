"""Independent original-XML audit of full or partial admitted NET selections."""
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'fresh_history_workflow_v1_stage_0_2026-10-09'
receipt=json.loads((D/'verification.json').read_text())
for p,h in receipt['bindings'].items():assert sha(p)==h,p
ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json'
bp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_1_budgets.json'
g=R/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits/rr_graph.xml'
inv=read(g,sha(g))
q={row['connection_id']:row for row in json.loads(ep.read_text())['connections']}
budgets={row['connection_id']:Fraction(*row['exact_delay_s']) for row in json.loads(bp.read_text())}
data=json.loads((D/'result.json').read_text());rows=[]
for attempt in data['attempts']:
 paths={int(cid):path for cid,path in attempt['paths'].items()}
 owners=defaultdict(set);parents=defaultdict(set);nets=defaultdict(set)
 for cid,path in paths.items():
  assert cid in q
  query=q[cid];net=query['net_id'];nets[net].add(cid)
  assert path[0]==[query['source'],None] and path[-1][0]==query['sink']
  assert len({n for n,s in path})==len(path)
  r,c=inv.classes[inv.node_classes[query['source']]];delay=r*c/2
  for n,s in path:owners[n].add(net)
  for (u,_),(v,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,s))==1
   parents[net,v].add((u,s))
   r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
  assert delay<=budgets[cid]
 assert all(len(ns)<=int(inv.physical.nodes[n][1]) for n,ns in owners.items())
 assert all(len(ps)==1 for ps in parents.values())
 for net,cids in nets.items():assert cids=={cid for cid,x in q.items() if x['net_id']==net}
 assert len(paths)==attempt['admitted_connections']
 assert {x['net'] for x in attempt['failed_nets']}=={x['net_id'] for cid,x in q.items() if cid not in paths}
 rows.append(dict(attempt=attempt['attempt'],admitted_connections=len(paths),
                  failed_nets=len(attempt['failed_nets']),atomic_net_admission=True))
if data['paths'] is None:assert receipt['status']=='NO_COMPLETE_SELECTION'
else:
 assert {int(cid) for cid in data['paths']}==set(q)
 assert receipt['status']=='FOUND_REQUIRES_INDEPENDENT_FULL_GATES'
 assert data['paths']==data['attempts'][-1]['paths']
checked_events=0
edge={eid:arc for arc,eid in inv.physical.arcs.items()}
for attempt in data['attempts']:
 for event in attempt['events']:
  if event['status']!='FOUND':continue
  query=q[event['cid']];path=[[query['source'],None]]
  r,c=inv.classes[inv.node_classes[query['source']]];delay=r*c/2
  for eid in event['physical_edge_ids']:
   u,v,s=edge[eid];assert u==path[-1][0]
   assert inv.arc_multiplicities.get((u,v,s))==1
   path.append([v,s]);r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
  assert path[-1][0]==query['sink'] and len({n for n,s in path})==len(path)
  assert delay<=budgets[event['cid']]
  assert event.get('history_banned_node') not in {n for n,s in path}
  checked_events+=1
out=D/'independent_verification.json';assert not out.exists()
out.write_text(json.dumps(dict(rows=rows,checked_successful_search_events=checked_events,status=receipt['status'],
 bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(Path(__file__))},
 scope='All admitted paths original XML/Fraction budgets, unique NET capacity, shared parent, whole NET coverage. No native/STA acceptance claim.'),indent=2)+'\n')
print(rows,flush=True)
