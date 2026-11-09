"""Full native cost binding audit using compact read-only node metadata."""
import json,time,sys
from pathlib import Path
from array import array
from types import SimpleNamespace
from collections import Counter
from collections.abc import Mapping
import xml.etree.ElementTree as ET
root=Path('experiments/stereo_prospective_validation_2026-10-05');sys.path.insert(0,str((root/'source').resolve()))
from pre_route_endpoints import sha
from bound_indexed_cost import validate_binding
p=json.loads((root/'protocol.json').read_text());parent=root/'native_cost_binding';receipt=json.loads((parent/'receipt.json').read_text());assert receipt['exit_code']==0 and receipt['shared_inputs_unchanged']
out=root/'cost_binding_audit'
if out.exists():raise ValueError('fresh audit required')
inputs={'graph':p['inputs']['graph'],**{name:{'path':str((parent/name).resolve()),'sha256':h} for name,h in receipt['outputs'].items()}}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());assert sha(root/'source/bound_indexed_cost.py')==p['frozen_sources']['bound_indexed_cost.py'];out.mkdir();start=time.monotonic()
(out/'protocol.json').write_text(json.dumps({'inputs':inputs,'native_export_protocol_sha256':sha(parent/'protocol.json'),'frozen_validator_sha256':p['frozen_sources']['bound_indexed_cost.py'],'driver_sha256':sha(__file__),'scope':'all nodes cost/type/segment/layer binding; no route labels read'},indent=2)+'\n')
kinds=('SOURCE','SINK','OPIN','IPIN','CHANX','CHANY');types=array('B');segments=array('i');layers=array('i');definitions={};stack=[]
with open(inputs['graph']['path'],'rb') as f:
 for event,e in ET.iterparse(f,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent_element=stack[-2] if len(stack)>1 else None
  if e.tag=='segment' and parent_element is not None and parent_element.tag=='segments':definitions[int(e.attrib['id'])]=ET.tostring(e,encoding='unicode')
  elif e.tag=='node' and parent_element is not None and parent_element.tag=='rr_nodes':
   assert int(e.attrib['id'])==len(types);types.append(kinds.index(e.attrib['type']));seg=e.find('segment');segments.append(int(seg.attrib['segment_id']) if seg is not None else -1);loc=e.find('loc');assert loc is not None;layers.append(int(loc.attrib.get('layer','0')))
  if e.tag=='rr_nodes':break
  if parent_element is not None and parent_element.tag in {'rr_nodes','segments','switches','block_types','grid','channels'}:parent_element.remove(e);e.clear()
  stack.pop()
class Nodes(Mapping):
 def __len__(self):return len(types)
 def __iter__(self):return iter(range(len(types)))
 def __contains__(self,key):return type(key) is int and 0<=key<len(types)
 def __getitem__(self,key):
  if key not in self:raise KeyError(key)
  return SimpleNamespace(type=kinds[types[key]],segment_id=None if segments[key]<0 else segments[key],location=(('layer',str(layers[key])),))
graph=SimpleNamespace(nodes=Nodes(),segments=definitions,sha256=inputs['graph']['sha256']);text=Path(inputs['rr_indexed_data.echo']['path']).read_text();csv=Path(inputs['routecast_node_cost_indices.csv']['path']).read_text();identity={'graph_sha256':graph.sha256,'table_sha256':inputs['rr_indexed_data.echo']['sha256'],'bindings_sha256':inputs['routecast_node_cost_indices.csv']['sha256']}
norm,rows,indices,_=validate_binding(graph,text,csv,identity);assert len(indices)==3593250;assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
report={'all_native_node_bindings_verified':True,'nodes':len(indices),'cost_classes':len(rows),'normalization':str(norm),'native_index_counts':dict(Counter(indices.values())),'channel_segment_counts':dict(Counter(segments[i] for i in range(len(types)) if types[i]>=4)),'identity':identity,'wall_s':time.monotonic()-start,'scope':'full per-node architectural cost/type/segment/layer binding; not predictor accuracy or native route QoR'};(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
