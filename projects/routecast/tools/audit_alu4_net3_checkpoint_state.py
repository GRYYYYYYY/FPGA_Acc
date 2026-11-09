"""Independent all-node and whole-tree audit of a closed net checkpoint."""
import json
from pathlib import Path
from collections import defaultdict
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
from net_union_topology import diagnose
from pin_choice_catalog import PinChoiceCatalog
from buffered_delay_cost import BufferedDelayCost
from pre_route_endpoints import sha
out=Path('experiments/alu4_free_pin_cohort_net3_audit_2026-10-05');path=Path('experiments/alu4_free_pin_cohort_2026-10-05/net_3_prediction.json');identity=sha(path);pred=json.loads(path.read_text());before=json.loads(Path('experiments/alu4_free_pin_budget_trial_2026-10-05/prediction.json').read_text());old={r['connection_id']:r for r in before['connections']};g=read_rr_graph('work/alu4_validation_capture_2026-10-05/rr_graph.xml');e=json.loads(Path('experiments/alu4_validation_capture_2026-10-05/endpoints.json').read_text());physical=audit(g,e,pred);catalog=PinChoiceCatalog(g);model=BufferedDelayCost(g);pins=defaultdict(set);changed=[]
for r in pred['connections']:
 b=old[r['connection_id']];bw=catalog.witness(b['source'],b['sink'],b['physical_edge_ids']);w=catalog.witness(r['source'],r['sink'],r['physical_edge_ids']);assert bw['selected_opin_ptc']==w['selected_opin_ptc'];pins[r['sink'],w['selected_ipin_ptc']].add(r['net_id']);assert model.path_delay(r['source'],r['physical_edge_ids'])<=model.path_delay(b['source'],b['physical_edge_ids'])
 if r['net_id']!=3:assert r==b
 if r!=b:changed.append(r['connection_id'])
assert all(len(v)==1 for v in pins.values());assert all(v<=g.nodes[int(n)].capacity for n,v in pred['node_occupancy'].items());top=diagnose(g,pred);assert all(not n['internal_multi_incoming_nodes'] and not n['cyclic_union'] and not n['source_has_incoming'] and n['all_nodes_source_reachable'] for n in top['nets']);assert sha(path)==identity
record={'checkpoint_sha256':identity,'source_sha256':sha(__file__),'changed_connections':changed,'physical_audit':physical,'pin_overuse':0,'all_node_type_capacity_overflow':0,'whole_net_count':len(top['nets']),'all2331_fixed_source_and_nonincreasing_RC_verified':True,'outside_net3_records_unchanged':True,'scope':'Closed completed-net checkpoint only, not final1012 trial or native STA'};(out/'state_audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='physical_audit'}),flush=True)
