"""Budget-valid conflict-node detours expand the finite path bank only."""
import json
from fractions import Fraction as F
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_bounded_wire_search_v1 import NativeBoundedSearch
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'online_cost_replay_v1_adder_online_candidate_bank_v1_2026-10-09';D=E/'online_cost_replay_v1_adder_online_detour_bank_v1_2026-10-09';D.mkdir(exist_ok=False);proof=json.loads((B/'verification.json').read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());bindings={**proof['bindings'],str(B/'verification.json'):sha(B/'verification.json')}
from native_resume_prototype.source_binding_v2 import closure
bindings.update(closure([Path(__file__)]));bound=B/'bounds_verification.json';cert=json.loads(bound.read_text());assert all(sha(p)==h for p,h in cert['bindings'].items());bindings.update(cert['bindings']);bindings[str(bound)]=sha(bound)
ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';g,h,nodes,f,rc,_=load_endpoints(ep0);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
edge={f['edge_ids'][i]:(u,f['dest_ranks'][i],f['switch_ids'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};search=NativeBoundedSearch(rc,length);bindings.update(search.bindings);rows=[]
try:
 for step in range(1,4):
  ep=ep0 if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';queries={q['connection_id']:q for q in json.loads(ep.read_text())['connections']};budgetpath=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json';budgets={b['connection_id']:F(*b['exact_delay_s']) for b in json.loads(budgetpath.read_text())};v=json.loads((B/f'step_{step}.json').read_text());bank=v['bank'];attempts=[]
  for conflict in v['required_node_capacity_conflicts']:
   node=conflict['node']
   for cid,q in sorted(queries.items()):
    candidates=bank[str(cid)]
    if q['net_id'] not in conflict['required_net_ids'] or not all(any(n==node for n,s in c['path']) for c in candidates):continue
    assert node!=q['source'];value=budgets[cid]*rc.scale;result=search.query(q['source'],q['sink'],value.numerator//value.denominator,Counter({node:f['capacities'][node]}),set(),{},1000000,sum(length.values())+1);attempts.append(dict(connection_id=cid,forbidden_node=node,**result))
    if result['status']!='FOUND':continue
    path=[[q['source'],None]];current=q['source']
    for eid in result['physical_edge_ids']:
     u,n,s=edge[eid];assert u==current;path.append([n,s]);current=n
    assert node not in {n for n,s in path}
    if not any(c['path']==path for c in candidates):candidates.append(dict(origin='conflict_detour',path=path,exact_delay_s=[F(result['delay'],rc.scale).numerator,F(result['delay'],rc.scale).denominator],forbidden_node=node))
  required=defaultdict(set)
  for cid,candidates in bank.items():
   for node in set.intersection(*[{n for n,s in c['path']} for c in candidates]):required[node].add(queries[int(cid)]['net_id'])
  conflicts=[dict(node=n,capacity=f['capacities'][n],required_net_ids=sorted(nets)) for n,nets in sorted(required.items()) if len(nets)>f['capacities'][n]]
  out=D/f'step_{step}.json';out.write_text(json.dumps(dict(bank=bank,attempts=attempts,empty_connection_ids=[],required_node_capacity_conflicts=conflicts),indent=2)+'\n')
  for p in (ep,budgetpath,out):bindings[str(p)]=sha(p)
  row=dict(step=step,attempts=len(attempts),status_counts=dict(Counter(a['status'] for a in attempts)),eligible_candidates=sum(map(len,bank.values())),remaining_required_capacity_conflicts=len(conflicts));rows.append(row);print(row,flush=True)
finally:search.close()
for name in ('trial_adder_online_detour_bank_v1.py','native_bounded_wire_search_v1.py','class_cached_rc_endpoint_context_v1.py'):bindings[str(R/'tools'/name)]=sha(R/'tools'/name)
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Single-node detour candidates only; capacityrelaxed except forbidden node, original budgets fixed. No joint parent/capacity/wire feasible route or native acceptance inferred.'),indent=2)+'\n')
