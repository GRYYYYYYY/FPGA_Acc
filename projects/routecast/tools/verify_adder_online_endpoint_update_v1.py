"""Independent original XML/Fraction replay of every generated online path."""
import json
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
from unified_rr_audit_inventory_v2 import read
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_online_endpoint_update_v1_2026-10-09';D=E/'adder_online_endpoint_update_verification_v1_2026-10-09';D.mkdir(exist_ok=False);p=B/'verification.json';report=json.loads(p.read_text());bindings={**report['bindings'],str(p):sha(p),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());inv=None;rows=[]
for step in range(1,4):
 meta=json.loads((E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json').read_text());q={x['connection_id']:x for x in meta['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads((E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json').read_text())};doc=json.loads((B/f'step_{step}.json').read_text())
 if inv is None:inv=read(meta['inputs']['graph']['path'],meta['graph_sha256'])
 checked=0
 for event in doc['events']:
  if event['status']!='FOUND':continue
  cid=event['connection_id'];path=event['path'];assert path[0]==[q[cid]['source'],None] and path[-1][0]==q[cid]['sink'] and len({n for n,s in path})==len(path);r,c=inv.classes[inv.node_classes[q[cid]['source']]];delay=r*c/2;ids=[]
  for (u,_),(v,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,s))==1;ids.append(inv.physical.arcs[u,v,s]);r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
  assert ids==event['physical_edge_ids'] and delay<=budgets[cid];checked+=1
 assert not doc['committed'] and doc['state'] is None and doc['events'][-1]['connection_id']==doc['failed_connection'];rows.append(dict(step=step,generated_paths_fraction_physical_budget_pass=checked,terminal_status=doc['events'][-1]['status'],failed_connection=doc['failed_connection'],no_candidate_published=True))
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Independent every generated path original arc/Fraction/budget proof; no complete candidate, native certification or global infeasibility conclusion.'),indent=2)+'\n');print(json.dumps(rows,indent=2))
