"""Check all individually budget-feasible failed native branches against full existing tree/capacity."""
import json
from collections import defaultdict,Counter
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from immutable_xml_prediction_audit import ImmutableXMLAudit
R=Path(__file__).resolve().parents[1]
F=R/'experiments/branch_budget_feasibility_v1_2026-10-08/diagnosis.json';d=json.loads(F.read_text());assert all(sha(f)==h for f,h in d['bindings'].items())
bindings={**d['bindings'],str(F):sha(F),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/immutable_xml_prediction_audit.py'):sha(R/'tools/immutable_xml_prediction_audit.py'),str(R/'tools/native_route_ledger_import_compact.py'):sha(R/'tools/native_route_ledger_import_compact.py')}
P=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';case=next(c for c in json.loads(P.read_text())['cases'] if c['width']==32 and c['index']==2)
ep=json.loads(Path(case['target']).read_text());graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ep['graph_sha256'])
route=R/'experiments/native_resume_branch_partial_v8_2026-10-08/resume/output.route';paths=physical_paths(route);observed={}
for name,branches in paths.items():
 for branch in branches:
  key=(name,branch[0][0],branch[-1][0]);assert key not in observed;observed[key]=branch
queries={q['connection_id']:q for q in ep['connections']};original={cid:observed[ep['net_names'][str(q['net_id'])],q['source'],q['sink']] for cid,q in queries.items()}
assert len(original)==1929
by_net=defaultdict(dict)
for cid,path in original.items():by_net[queries[cid]['net_id']][cid]=path
unions={net:{n for path in records.values() for n,s in path} for net,records in by_net.items()};ledger=Counter(n for union in unions.values() for n in union)
assert all(v<=xml.graph.nodes[n].capacity for n,v in ledger.items())
floors=json.loads((R/'experiments/branch_budget_target_rr_floors_w32_m2_2026-10-08/receipt.json').read_text());floor_rows={x['query']['connection_id']:x for x in floors['rows']}
rows=[]
for item in d['native_failure_classification']:
 cid=item['connection_id'];q=queries[cid];net=q['net_id'];cert=item['certified_floor']
 if not cert['relaxed_budget_feasible']:
  rows.append(dict(connection_id=cid,status='CERTIFIED_RELAXED_BUDGET_INFEASIBLE'));continue
 if item['resume']['budget_pass']:
  rows.append(dict(connection_id=cid,status='CURRENT_RESUME_ALREADY_BUDGET_SAFE'));continue
 floor=floor_rows[cid];u=q['source'];replacement=[(u,None)]
 for eid in floor['physical_edge_ids']:
  e=xml.graph.edges[eid];assert e.source==u;u=e.sink;replacement.append((u,e.switch_id))
 assert u==q['sink'] and len({n for n,s in replacement})==len(replacement)
 candidate={**by_net[net],cid:replacement};parents={};conflicts=[]
 for other,path in candidate.items():
  for (u,_),(v,switch) in zip(path,path[1:]):
   pair=(u,switch)
   if v in parents and parents[v]!=pair:conflicts.append(dict(node=v,connection_id=other,first_parent=parents[v],second_parent=pair))
   else:parents[v]=pair
 used={n for path in candidate.values() for n,s in path};new_ledger=ledger.copy();new_ledger.subtract(unions[net]);new_ledger.update(used)
 overflow=[dict(node=n,occupancy=count,capacity=xml.graph.nodes[n].capacity) for n,count in new_ledger.items() if count>xml.graph.nodes[n].capacity]
 minimum=Fraction(floor['minimum_integer'],floors['scale']);assert minimum*10**9<=Fraction(cert['budget_ns'])
 rows.append(dict(connection_id=cid,net_id=net,status='SINGLE_REPLACEMENT_TREE_CAPACITY_SAFE' if not conflicts and not overflow else 'REQUIRES_JOINT_REPAIR',physical_edge_ids=floor['physical_edge_ids'],minimum_seconds=str(minimum),budget_ns=cert['budget_ns'],shared_parent_conflicts=conflicts,capacity_overflow_nodes=overflow,remaining_connections_unchanged=1928))
D=R/'experiments/branch_budget_single_replacement_v1_2026-10-08';D.mkdir(exist_ok=False)
assert all(sha(f)==h for f,h in bindings.items())
(D/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,complete_native_failure_union=len(rows),rows=rows,scope='Each one-branch proposal checked separately against all current native paths; parent/capacity budget model diagnostic only, no simultaneous proposals, native serialization/acceptance, STA, or whole-cohort budget success.'),indent=2)+'\n')
print([(x['connection_id'],x['status'],len(x.get('shared_parent_conflicts',[])),len(x.get('capacity_overflow_nodes',[]))) for x in rows])
