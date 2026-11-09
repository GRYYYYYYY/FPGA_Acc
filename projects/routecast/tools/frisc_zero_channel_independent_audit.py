"""Independent final-state checks; no native VPR timing or legality claim."""
import json,time
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
from pin_choice_catalog import PinChoiceCatalog
from net_union_topology import diagnose
start=time.monotonic();out=Path('experiments/frisc_zero_channel_independent_audit_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files=['experiments/frisc_final_one_candidate_commit_2026-10-05/prediction.json','experiments/frisc_sequential_pin_compatible_round4_2026-10-05/prediction.json','work/frisc_graph_capture_2026-10-05/rr_graph.xml','experiments/frisc_endpoints_2026-10-05/endpoints.json'];inputs={p:sha(p) for p in files};g=read_rr_graph(files[2]);p=json.loads(Path(files[0]).read_text());base=json.loads(Path(files[1]).read_text());checked=audit(g,json.loads(Path(files[3]).read_text()),p);catalog=PinChoiceCatalog(g);old={r['connection_id']:r for r in base['connections']};pin_users=defaultdict(set);pin_requests=defaultdict(list);changed=0
for r in p['connections']:
 a=catalog.witness(r['source'],r['sink'],r['physical_edge_ids']);o=old[r['connection_id']];b=catalog.witness(o['source'],o['sink'],o['physical_edge_ids']);assert all(a[k]==b[k] for k in ('selected_opin_ptc','selected_ipin_ptc'));changed+=r['physical_edge_ids']!=o['physical_edge_ids'];key=(r['sink'],a['selected_ipin_ptc']);pin_users[key].add(r['net_id']);pin_requests[key].append(r['connection_id'])
pin_overuse=sum(max(0,len(v)-1) for v in pin_users.values());assert pin_overuse==0
bytype=Counter();overloaded=[]
for n,v in p['node_occupancy'].items():
 node=g.nodes[int(n)];extra=max(0,v-node.capacity)
 if extra:bytype[node.type]+=extra;overloaded.append({'rr_node':int(n),'type':node.type,'capacity':node.capacity,'demand':v})
assert not bytype.get('CHANX',0) and not bytype.get('CHANY',0)
topology=diagnose(g,p);assert all(not r['internal_multi_incoming_nodes'] and not r['cyclic_union'] and not r['source_has_incoming'] and r['all_nodes_source_reachable'] for r in topology['nets'])
assert all(sha(path)==h for path,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());r={'physical_audit':checked,'changed_paths_from_round4':changed,'all_current_physical_pins_unchanged_from_round4':True,'physical_input_pin_unique_net_overuse':pin_overuse,'capacity_overuse_by_rr_type':dict(bytype),'overloaded_resources':overloaded,'net_count':len(topology['nets']),'all_net_structural_checks_passed':True,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'full_wall_s':time.monotonic()-start,'scope':'complete individual RR paths, unique-net capacity, physical pins and net union topology; not native VPR legality, packed internal rerouting or STA'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
