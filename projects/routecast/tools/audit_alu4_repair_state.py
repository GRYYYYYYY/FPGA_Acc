"""Independent full physical, pin, score and union check of a repair state."""
import argparse,json
from pathlib import Path
from collections import defaultdict
from rr_graph import read_rr_graph
from pin_choice_catalog import PinChoiceCatalog
from physical_prediction_audit import audit
from net_union_topology import diagnose
from feedback_scores import scores
from pre_route_endpoints import sha
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();out=a.directory;pred=json.loads((out/'prediction.json').read_text());g=read_rr_graph('work/alu4_validation_capture_2026-10-05/rr_graph.xml');e=json.loads(Path('experiments/alu4_validation_capture_2026-10-05/endpoints.json').read_text());physical=audit(g,e,pred);catalog=PinChoiceCatalog(g);users=defaultdict(set)
for row in pred['connections']:
 w=catalog.witness(row['source'],row['sink'],row['physical_edge_ids']);users[w['sink_class'],w['selected_ipin_ptc']].add(row['net_id'])
over=sum(max(0,len(u)-1) for u in users.values());assert over==0;score=scores(g,e,pred['node_occupancy']);receipt=json.loads((out/'receipt.json').read_text());assert score==receipt.get('scores_after',receipt.get('final_scores'));top=diagnose(g,pred);assert all(not n['internal_multi_incoming_nodes'] and not n['cyclic_union'] and not n['source_has_incoming'] and n['all_nodes_source_reachable'] for n in top['nets']);r={'prediction_sha256':sha(out/'prediction.json'),'source_sha256':sha(__file__),'unique_net_pin_overuse':over,'scores':score,'physical_audit':physical,'topology':top,'scope':'Full predicted physical/pin/unique-net/tree state; residual channel capacity and native timing still separate'};(out/'independent_state_audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'scores':score,'pin_overuse':over,'nets':len(top['nets'])}),flush=True)
