"""All68 attaining baseline-path blockers under fixed outside NET ownership."""
import json
from collections import defaultdict,Counter
from pathlib import Path
from unified_rr_audit_inventory_v2 import read
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_capacity_budget_wholenet_repair_v1_2026-10-08';D=E/'adder_remaining_budget_blockers_v1_2026-10-08';D.mkdir(exist_ok=False)
p=B/'verification.json';v=json.loads(p.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());bindings={**v['bindings'],str(p):sha(p)};summary=[];inv=None
for step in range(4):
 ep=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';meta=json.loads(ep.read_text());queries={q['connection_id']:q for q in meta['connections']}
 if inv is None:inv=read(meta['inputs']['graph']['path'],meta['graph_sha256'])
 edge={eid:key for key,eid in inv.physical.arcs.items()};statepath=B/f'step_{step}.json';state=json.loads(statepath.read_text());owners=defaultdict(set)
 for cid,path in state['state'].items():
  for n,s in path:owners[n].add(queries[int(cid)]['net_id'])
 assert {str(n):len(ns) for n,ns in owners.items()}==state['node_occupancy']
 pred=E/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json' if step==0 else E/f'adder_tree_2L032_move_sequence_audit_2026-10-06/step_{step}_prediction.json';paths={q['connection_id']:q for q in json.loads(pred.read_text())['connections']};rows=[];frequency=Counter()
 for cid in state['violation_ids']:
  q=queries[cid];nodes=[q['source']];cursor=q['source']
  for eid in paths[cid]['physical_edge_ids']:
   u,n,s=edge[eid];assert u==cursor;nodes.append(n);cursor=n
  assert cursor==q['sink'];blocked=[]
  for n in nodes:
   outside=owners[n]-{q['net_id']};cap=int(inv.physical.nodes[n][1])
   if len(outside)>=cap:blocked.append(dict(node=n,type=inv.physical.nodes[n][0],capacity=cap,outside_owner_nets=sorted(outside)))
  neighbors=sorted({net for x in blocked for net in x['outside_owner_nets']});frequency.update(neighbors)
  rows.append(dict(connection_id=cid,net_id=q['net_id'],blocked_nodes=blocked,conflict_neighbor_nets=neighbors,attaining_path_available_after_own_net_release=not blocked))
 out=D/f'step_{step}_blockers.json';out.write_text(json.dumps(dict(rows=rows,neighbor_connection_incidence={str(n):c for n,c in sorted(frequency.items())}),indent=2)+'\n')
 for f in (ep,pred,statepath,out):bindings[str(f)]=sha(f)
 summary.append(dict(step=step,remaining_connections=len(rows),baseline_paths_blocked_by_outside_capacity=sum(bool(x['blocked_nodes']) for x in rows),distinct_neighbor_nets=len(frequency),largest_incidence=frequency.most_common(5)));print(summary[-1],flush=True)
assert sum(x['remaining_connections'] for x in summary)==68 and all(sha(f)==h for f,h in bindings.items())
for n in ('diagnose_adder_remaining_budget_blockers_v1.py','unified_rr_audit_inventory_v2.py','pre_route_endpoints.py'):
 f=R/'tools'/n;bindings[str(f)]=sha(f)
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=summary,scope='All remaining68 baseline attaining path witnesses diagnosed against complete uniqueNET owner sets. Fixed-state saturated outside resources identify possible release neighborhoods, not necessary blockers on every path or global infeasibility. No route mutation/new candidate/native/runtime gain.'),indent=2)+'\n')
