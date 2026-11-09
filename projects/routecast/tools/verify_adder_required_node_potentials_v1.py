"""Independent original-XML Bellman potential proof, not search replay."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_required_node_potentials_v1_2026-10-09';receipt=json.loads((D/'receipt.json').read_text());assert all(sha(p)==h for p,h in receipt['bindings'].items());ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';m=json.loads(ep0.read_text());inv=read(m['inputs']['graph']['path'],m['graph_sha256']);n=len(inv.node_classes);rows=[];weights={};checked=0
for step in range(4):
 ep=ep0 if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';queries={q['connection_id']:q for q in json.loads(ep.read_text())['connections']};budgets={b['connection_id']:F(*b['exact_delay_s']) for b in json.loads((E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json').read_text())};v=json.loads((D/f'step_{step}.json').read_text());required={}
 for cert in v['certificates']:
  cid=cert['connection_id'];q=queries[cid];blocked=cert['blocked_node'];assert q['net_id']==cert['net_id'];assert 0<=blocked<n
  if cert['terminal_required']:assert blocked in (q['source'],q['sink'])
  else:
   p=cert['potentials'];scale=cert['scale'];assert type(scale)is int and scale>0 and len(p)==n and all(type(x)is int and x>=0 for x in p)
   rr,cc=inv.classes[inv.node_classes[q['source']]];assert F(p[q['source']],scale)<=rr*cc/2
   for u,w,s in inv.physical.arcs:
    if blocked in (u,w) or int(inv.physical.nodes[u][1])<=0 or int(inv.physical.nodes[w][1])<=0:continue
    key=(inv.node_classes[w],s,scale)
    if key not in weights:
     rr,cc=inv.classes[key[0]];sr,td=inv.electrical_switches[s];value=((sr+rr/2)*cc+td)*scale;assert value.denominator==1 and value>=0;weights[key]=value.numerator
    assert p[w]<=p[u]+weights[key];checked+=1
   lower=F(p[q['sink']],scale);assert lower>budgets[cid] and lower==F(cert['sink_lower_bound_seconds'])
  required.setdefault(blocked,set()).add(q['net_id'])
 for conflict in v['conflicts']:
  node=conflict['node'];nets=required.get(node,set());assert sorted(nets)==conflict['certified_required_net_ids'] and int(inv.physical.nodes[node][1])==conflict['capacity'];assert conflict['all_model_budget_capacity_infeasible']==(len(nets)>conflict['capacity'])
 assert any(c['all_model_budget_capacity_infeasible'] for c in v['conflicts'])
 rows.append(dict(step=step,independent_required_node_certificates=len(v['certificates']),certified_capacity_conflicts=sum(c['all_model_budget_capacity_infeasible'] for c in v['conflicts']),joint_original_model_budgets_infeasible=True))
assert all(sha(p)==h for p,h in receipt['bindings'].items())
out=dict(bindings={str(p):sha(p) for p in (D/'receipt.json',Path(__file__),R/'tools/unified_rr_audit_inventory_v2.py')},rows=rows,all_allowed_original_arc_bellman_inequalities_checked=checked,scope='All4 archived additive buffered-RC perconnection budget sets incompatible with original uniqueNET node capacities over all physical paths, not merely finitebank. No STA/userclock/HDL/hardware infeasibility claim.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
