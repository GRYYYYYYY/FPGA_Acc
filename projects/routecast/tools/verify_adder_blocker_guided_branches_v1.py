"""Independent original-XML witness replay and whole-owner exclusion checks."""
import json
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_blocker_guided_branches_v1_2026-10-08';r=json.loads((D/'receipt.json').read_text());assert all(sha(p)==h for p,h in r['bindings'].items())
m=json.loads((E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json').read_text());inv=read(m['inputs']['graph']['path'],m['graph_sha256']);edges={eid:arc for arc,eid in inv.physical.arcs.items()};rows=[]
for step in range(4):
 ep=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';queries={q['connection_id']:q for q in json.loads(ep.read_text())['connections']};budget={q['connection_id']:F(*q['exact_delay_s']) for q in json.loads((E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json').read_text())}
 v=json.loads((D/f'step_{step}.json').read_text());old=json.loads((E/f'adder_failure_priority_retry_v1_2026-10-08/step_{step}.json').read_text());assert v['state']==old['state'];witnesses=Counter();branches=0
 for e in v['events']:
  assert not e['committed'];excluded={a['connection_id']:a['excluded_nodes'] for a in e['attempts'] if a['excluded_nodes']}
  if excluded:
   branches+=1;assert len({queries[cid]['net_id'] for cid in excluded})==1 and len({tuple(ns) for ns in excluded.values()})==1 and all(len(ns)==1 for ns in excluded.values())
  for a in e['attempts']:
   if a['status']=='FOUND':assert not {edges[i][1] for i in a['physical_edge_ids']}.intersection(a['excluded_nodes'])
  w=e.get('capacity_relaxed_witness')
  if w is None:continue
  witnesses[w['status']]+=1
  if w['status']!='FOUND':continue
  q=queries[e['attempts'][-1]['connection_id']];node=q['source'];rr,cc=inv.classes[inv.node_classes[node]];delay=rr*cc/2;seen={node}
  node=q['source']
  for eid in w['physical_edge_ids']:
   u,n,s=edges[eid];assert u==node and n not in seen;seen.add(n);node=n
   rr,cc=inv.classes[inv.node_classes[n]];sr,td=inv.electrical_switches[s];delay+=(sr+rr/2)*cc+td
  assert node==q['sink'] and delay<=budget[q['connection_id']]
 rows.append(dict(step=step,group_attempts=len(v['events']),witness_status_counts=dict(witnesses),branches_reaching_excluded_owner=branches,state_exactly_unchanged=True))
out=dict(bindings={str(p):sha(p) for p in (D/'receipt.json',Path(__file__))},rows=rows,scope='Independent Fraction/physical witness replay, owner-level single-node exclusions and unchanged accepted states. Diagnostic witnesses never installed; bounded siblings not complete search.')
(D/'branch_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
