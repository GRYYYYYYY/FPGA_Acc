"""Independent streamed XML electrical decomposition vs production CSR increments."""
import sys,json,xml.etree.ElementTree as E
from pathlib import Path
from array import array
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from buffered_rc_node_classes import read,arc_delay
endpoint=R/'experiments/ethernet_native_demand_v1_2026-10-08/endpoints.json'
protocol=R/'experiments/ethernet_switch_objective_ablation_prereg_v1_2026-10-08/protocol.json'
p=json.loads(protocol.read_text());assert all(sha(k)==v for k,v in p['bindings'].items())
graph,digest,nodes,f,rc,queries=load_endpoints(endpoint)
ids,classes,switches,other_digest=read(graph);assert digest==other_digest
objective=array('Q',(rc.initial(v) for v in f['dest_ranks']))
inverse=array('Q',[0])*len(f['edge_ids'])
for slot,eid in enumerate(f['edge_ids']):inverse[eid]=slot
components={};positive=zero=checked=0;stack=[]
for event,e in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 if e.tag=='edge':
  slot=inverse[checked];v=int(e.get('sink_node'));sid=int(e.get('switch_id'))
  assert f['edge_ids'][slot]==checked and f['dest_ranks'][slot]==v and f['switch_ids'][slot]==sid
  u=int(e.get('src_node'));assert f['row_offsets'][u]<=slot<f['row_offsets'][u+1]
  key=(ids[v],sid)
  if key not in components:
   nr,nc=classes[ids[v]];sr,td=switches[sid]
   wire=nr*nc/2;sw=sr*nc+td;full=arc_delay(classes,switches,ids[v],sid)
   assert full==wire+sw and wire>=0 and sw>=0
   components[key]=(rc.encode(wire),rc.encode(sw),rc.encode(full))
  wire,sw,full=components[key];assert objective[slot]==wire and rc.increments[slot]==full==wire+sw
  positive+=sw>0;zero+=sw==0;checked+=1
 if e.tag in {'node','edge'}:
  if len(stack)>1:stack[-2].remove(e)
  e.clear()
 stack.pop()
assert checked==len(f['edge_ids']) and positive+zero==checked
out=R/'experiments/ethernet_switch_components_v1_2026-10-08';out.mkdir()
file=out/'objective.bin';file.write_bytes(objective.tobytes())
bindings={**closure([Path(__file__)]),str(endpoint):sha(endpoint),str(graph):sha(graph),str(protocol):sha(protocol),str(file):sha(file)}
assert all(sha(k)==v for k,v in bindings.items())
(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,all_original_XML_arcs_and_electrical_components_exact_pass=True,original_scale=rc.scale,arcs=checked,nodes=len(ids),physical_queries=len(queries),positive_switch_components=positive,zero_switch_components=zero,objective_path=str(file),objective_sha256=sha(file),objective_byteorder=sys.byteorder,objective_itemsize=objective.itemsize,scope='Every original XML arc authenticated against CSR and independent XML RC classes/switches; wire objective plus removed switch contribution equals original raw increment exactly on unchanged lattice. Not a prediction/route/fullworkflow gain result.'),indent=2)+'\n')
print('PASS switch component decomposition',checked,positive,zero)
