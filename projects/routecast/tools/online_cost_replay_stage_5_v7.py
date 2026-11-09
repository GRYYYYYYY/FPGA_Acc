"""Recompute finite-bank necessary-node capacity certificates independently."""
import json,xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'online_cost_replay_v7_adder_online_candidate_bank_v1_2026-10-09';report=json.loads((D/'verification.json').read_text());assert all(sha(p)==h for p,h in report['bindings'].items());ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';m=json.loads(ep0.read_text());g=Path(m['inputs']['graph']['path']);cap={int(n.get('id')):int(n.get('capacity')) for n in ET.parse(g).getroot().find('rr_nodes')};rows=[]
from fractions import Fraction as F
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
inv=read(g,m['graph_sha256'])
for step in range(1,4):
 v=json.loads((D/f'step_{step}.json').read_text());ep=ep0 if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';queries={str(q['connection_id']):q for q in json.loads(ep.read_text())['connections']};bp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json';budgets={str(x['connection_id']):F(*x['exact_delay_s']) for x in json.loads(bp.read_text())};required=defaultdict(set);checked=0;assert set(v['bank'])==set(queries) and not v['empty_connection_ids']
 for cid,candidates in v['bank'].items():
  assert candidates
  for candidate in candidates:
   path=candidate['path'];q=queries[cid];assert path[0]==[q['source'],None] and path[-1][0]==q['sink'] and len({n for n,s in path})==len(path)
   r,c=inv.classes[inv.node_classes[q['source']]];delay=r*c/2
   for (u,_),(dest,sw) in zip(path,path[1:]):
    assert inv.arc_multiplicities.get((u,dest,sw))==1 and cap[dest]>0;r,c=inv.classes[inv.node_classes[dest]];sr,td=inv.electrical_switches[sw];delay+=(sr+r/2)*c+td
   assert delay==F(*candidate['exact_delay_s']) and delay<=budgets[cid];checked+=1
  sets=[set(n for n,s in c['path']) for c in candidates]
  for node in set.intersection(*sets):required[node].add(queries[cid]['net_id'])
 expected=[dict(node=n,capacity=cap[n],required_net_ids=sorted(nets)) for n,nets in sorted(required.items()) if len(nets)>cap[n]]
 assert expected==v['required_node_capacity_conflicts'] and expected
 rows.append(dict(step=step,finite_bank_infeasible=True,checked_capacity_certificates=len(expected),independent_physical_fraction_candidates=checked))
assert sha(g)==m['graph_sha256'];out=dict(bindings={**report['bindings'],**closure([Path(__file__)]),**{str(p):sha(p) for p in (D/'verification.json',Path(__file__),g)}},rows=rows,scope='Each required NET must occupy node under every candidate choice for at least one demand. Distinct requiredNET count exceeds original capacity; finitebank infeasibility only, no allpaths/global proof.')
(D/'bounds_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(rows)
