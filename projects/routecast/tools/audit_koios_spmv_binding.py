"""Streaming full-node binding audit; intentionally does not replay graph arcs."""
import json,time,shutil
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
from bound_indexed_cost import validate_binding
out=Path('experiments/koios_spmv_binding_audit_2026-10-04');parent=Path('experiments/koios_spmv_cost_binding_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());assert r['exit_code']==0 and r['original_inputs_unchanged'] and r['protocol_sha256']==sha(parent/'protocol.json')
inputs={k:{'path':str((parent/k).resolve()),'sha256':v} for k,v in r['outputs'].items()};assert all(sha(v['path'])==v['sha256'] for v in inputs.values());out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'inputs':inputs,'scope':'all physical RR node IDs/types/segments and native per-node cost-index bindings; edges/path legality/accuracy not replayed','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic();nodes={};segments={};stack=[]
for event,e in ET.iterparse(inputs['rr_graph.xml']['path'],events=('start','end')):
 if event=='start':stack.append(e);continue
 if e.tag=='segment' and len(stack)>1 and stack[-2].tag=='segments':segments[int(e.attrib['id'])]=ET.tostring(e,encoding='unicode')
 if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
  n=int(e.attrib['id']);assert n not in nodes;segment=e.find('segment');nodes[n]=SimpleNamespace(type=e.attrib['type'],segment_id=int(segment.attrib['segment_id']) if segment is not None else None,location=tuple(e.find('loc').attrib.items()));stack[-2].remove(e);e.clear()
 if e.tag=='rr_nodes':break
 stack.pop()
graph=SimpleNamespace(nodes=nodes,segments=segments,sha256=inputs['rr_graph.xml']['sha256']);text=Path(inputs['rr_indexed_data.echo']['path']).read_text();csv=Path(inputs['routecast_node_cost_indices.csv']['path']).read_text();identity={'graph_sha256':graph.sha256,'table_sha256':inputs['rr_indexed_data.echo']['sha256'],'bindings_sha256':inputs['routecast_node_cost_indices.csv']['sha256']};norm,rows,indices,_=validate_binding(graph,text,csv,identity);assert all(sha(v['path'])==v['sha256'] for v in inputs.values());(out/'binding_identity.json').write_text(json.dumps(identity,indent=2)+'\n');report={'protocol_sha256':sha(out/'protocol.json'),'all_native_node_bindings_pass':True,'physical_nodes':len(nodes),'cost_classes':len(rows),'normalization':str(norm),'native_index_counts':dict(Counter(indices.values())),'channel_segment_counts':dict(Counter(n.segment_id for n in nodes.values() if n.type in {'CHANX','CHANY'})),'orthogonal_refs':{i:row['ortho'] for i,row in rows.items() if row['type'] in {'CHANX','CHANY'}},'scope':'full nodes only; graph edges/native path/estimator quality not audited','inputs_unchanged':True,'wall_s':time.monotonic()-start,'binding_identity_sha256':sha(out/'binding_identity.json')};(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
