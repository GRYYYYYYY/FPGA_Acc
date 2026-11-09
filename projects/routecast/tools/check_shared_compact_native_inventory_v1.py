"""Full node/location/capacity and physical edge-order parity on all development RR graphs."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from shared_compact_native_inventory_v1 import Inventory
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/shared_compact_native_inventory_contract_v1_2026-10-07';out.mkdir();bindings=closure([Path(__file__)]);rows=[]
for name in ['bigkey','dsip','misex3']:
 ep=json.loads((R/f'experiments/mcnc_fresh_conversion_resident_v1_2026-10-07/{name}/endpoints.json').read_text());path=Path(ep['inputs']['graph']['path']);inventory=Inventory(path);reference=read_rr_graph(path);inventory.validate(path,ep['graph_sha256']);assert inventory.digest==reference.sha256
 assert set(inventory.nodes)==set(reference.nodes)
 for n,node in reference.nodes.items():
  assert inventory.nodes[n]==(node.type,dict(node.location));assert inventory.graph.nodes[n].capacity==node.capacity and inventory.graph.nodes[n].type==node.type
 assert len(inventory.edges)==len(reference.edges)
 for i,e in enumerate(reference.edges):assert inventory.edges[i]==(e.source,e.sink,e.switch_id)
 try:inventory.validate(path,'0'*64)
 except ValueError:pass
 else:raise AssertionError('wrong digest accepted')
 bindings[str(path)]=sha(path);rows.append({'name':name,'nodes':len(reference.nodes),'edges':len(reference.edges),'all_node_type_capacity_location_and_edge_order_pass':True});print(name,'PASS',flush=True)
 del inventory,reference
(out/'verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n')
