"""Exact truncated shortest-distance potentials certify budget-required nodes."""
import json,heapq
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_conflict_detour_bank_v1_2026-10-09';D=E/'adder_required_node_potentials_v1_2026-10-09';D.mkdir(exist_ok=False);proof=json.loads((B/'verification.json').read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());bindings={**proof['bindings'],str(B/'verification.json'):sha(B/'verification.json')}
ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';g,h,nodes,f,rc,_=load_endpoints(ep0);rows=[]
for step in range(4):
 ep=ep0 if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';queries={q['connection_id']:q for q in json.loads(ep.read_text())['connections']};budgetpath=E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json';budgets={b['connection_id']:F(*b['exact_delay_s']) for b in json.loads(budgetpath.read_text())};bank=json.loads((B/f'step_{step}.json').read_text());certs=[];conflicts=[]
 for conflict in bank['required_node_capacity_conflicts']:
  blocked=conflict['node'];owners=[]
  for owner in conflict['required_net_ids']:
   for cid,q in sorted(queries.items()):
    if q['net_id']!=owner or not all(any(n==blocked for n,s in c['path']) for c in bank['bank'][str(cid)]):continue
    value=budgets[cid]*rc.scale;cap=value.numerator//value.denominator+1
    dist=[cap]*len(nodes);source=q['source'];sink=q['sink'];dist[source]=min(cap,rc.initial(source));heap=[(dist[source],source)]
    if blocked in (source,sink):
     cert=dict(connection_id=cid,net_id=owner,blocked_node=blocked,terminal_required=True);owners.append(owner);certs.append(cert);break
    while heap:
     d,u=heapq.heappop(heap)
     if d!=dist[u] or d>=cap:continue
     for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
      v=f['dest_ranks'][slot]
      if u==blocked or v==blocked or f['capacities'][u]<=0 or f['capacities'][v]<=0:continue
      nd=d+rc.increments[slot]
      if nd<dist[v]:dist[v]=nd;heapq.heappush(heap,(nd,v))
    if dist[sink]>value:
     cert=dict(connection_id=cid,net_id=owner,blocked_node=blocked,terminal_required=False,scale=rc.scale,potentials=dist,sink_lower_bound_seconds=str(F(dist[sink],rc.scale)));certs.append(cert);owners.append(owner);break
  conflicts.append(dict(node=blocked,capacity=conflict['capacity'],certified_required_net_ids=owners,all_model_budget_capacity_infeasible=len(owners)>conflict['capacity']))
 out=D/f'step_{step}.json';out.write_text(json.dumps(dict(certificates=certs,conflicts=conflicts),indent=2)+'\n')
 for p in (ep,budgetpath,out):bindings[str(p)]=sha(p)
 row=dict(step=step,required_node_certificates=len(certs),all_model_budget_capacity_conflicts=sum(c['all_model_budget_capacity_infeasible'] for c in conflicts));rows.append(row);print(row,flush=True)
for name in ('trial_adder_required_node_potentials_v1.py','class_cached_rc_endpoint_context_v1.py'):bindings[str(R/'tools'/name)]=sha(R/'tools'/name)
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Candidate independent allarc shortest-distance potential certificates, pending independent XML/Fraction verification. Applies only original archived additive model budgets, not STA/userclock.'),indent=2)+'\n')
