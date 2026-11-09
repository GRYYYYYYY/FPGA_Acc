"""Full final-state fixed-source/allowed-target-pin and exact additive delay budget audit."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from pin_choice_catalog import PinChoiceCatalog
from buffered_delay_cost import BufferedDelayCost
from physical_prediction_audit import audit
from feedback_scores import scores
root=Path('experiments/alu4_free_pin_cohort_2026-10-05');receipt=json.loads((root/'receipt.json').read_text());protocol=json.loads((root/'protocol.json').read_text());assert sha(root/'protocol.json')==receipt['protocol_sha256'];assert sha(root/'prediction.json')==receipt['prediction_sha256'];assert all(sha(p)==h for p,h in receipt['input_sha256'].items())
g=read_rr_graph('work/alu4_validation_capture_2026-10-05/rr_graph.xml');catalog=PinChoiceCatalog(g);model=BufferedDelayCost(g);e=json.loads(Path('experiments/alu4_validation_capture_2026-10-05/endpoints.json').read_text());before=json.loads(Path('experiments/alu4_free_pin_budget_trial_2026-10-05/prediction.json').read_text());after=json.loads((root/'prediction.json').read_text());old={r['connection_id']:r for r in before['connections']};selected=set(protocol['connection_ids']);assert len(selected)==1012 and len(after['connections'])==len(old)==2331
eq={r['cid']:r for r in json.loads(Path('experiments/alu4_full_pin_equivalence_audit_2026-10-05/receipt.json').read_text())['checks']};pin_users={};changed=[]
for r in after['connections']:
 b=old[r['connection_id']];a=catalog.witness(b['source'],b['sink'],b['physical_edge_ids']);w=catalog.witness(r['source'],r['sink'],r['physical_edge_ids']);assert a['selected_opin_ptc']==w['selected_opin_ptc'];assert w['selected_ipin_ptc'] in eq[r['connection_id']]['physical_members'];pin_users.setdefault((r['sink'],w['selected_ipin_ptc']),set()).add(r['net_id'])
 if r['connection_id'] in selected:assert model.path_delay(r['source'],r['physical_edge_ids'])<=model.path_delay(b['source'],b['physical_edge_ids'])
 else:assert r==b
 if r!=b:changed.append(r['connection_id'])
assert all(len(nets)==1 for nets in pin_users.values());assert len(changed)==sum(q['committed'] for q in receipt['reports']);physical=audit(g,e,after);assert scores(g,e,after['node_occupancy'])==receipt['final_scores'];assert all(v<=g.nodes[int(n)].capacity for n,v in after['node_occupancy'].items())
r={'prediction_sha256':sha(root/'prediction.json'),'source_sha256':sha(__file__),'fixed_source_pin_connections_verified':2331,'exact_delay_budget_connections_verified':1012,'changed_connections':changed,'outside_cohort_unchanged':True,'all_node_types_capacity_overflow':0,'physical_audit':physical,'pin_overuse':0,'scope':'Additive buffered-RC budget transfer; not native STA equivalence or unseen-family QoR claim'};(root/'budget_transfer_audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='physical_audit'}),flush=True)
