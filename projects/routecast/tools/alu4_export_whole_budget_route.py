"""Export audited RR unions as VPR traceback text, preserving template net inventory."""
import json,re,time
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha,physical_maps
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
from net_union_topology import diagnose
start=time.monotonic();out=Path('experiments/alu4_whole_budget_route_export_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files={'prediction':'experiments/alu4_whole_net_budget_cohort_2026-10-05/prediction.json','graph':'work/alu4_validation_capture_2026-10-05/rr_graph.xml','endpoints':'experiments/alu4_validation_capture_2026-10-05/endpoints.json','template':'work/alu4_validation_capture_2026-10-05/alu4.route'}
inputs={p:sha(p) for p in files.values()};g=read_rr_graph(files['graph']);p=json.loads(Path(files['prediction']).read_text());e=json.loads(Path(files['endpoints']).read_text());audit(g,e,p);top=diagnose(g,p);assert all(not n['internal_multi_incoming_nodes'] and not n['cyclic_union'] and not n['terminal_multi_incoming_nodes'] for n in top['nets'])
types,grid,_=physical_maps(files['graph']);pin_names={tid:{v[2]:(k[0]+'.'+k[2]+'['+str(k[3])+']') for k,v in t['pins'].items()} for tid,t in types.items()}
text=Path(files['template']).read_text();parts=re.split(r'(?m)(?=^Net \d+ )',text);headers={};chunks={};native_sink_indices=defaultdict(list)
for chunk in parts[1:]:
 head=chunk.splitlines()[0];m=re.match(r'Net (\d+) \((.*)\)(.*)',head);assert m;name=m[2];headers[name]=head;chunks[name]=chunk
 for line in chunk.splitlines():
  match=re.match(r'Node:\s*(\d+)\s+SINK .*Net_pin_index:\s*(\d+)',line)
  if match:native_sink_indices[(name,int(match[1]))].append(int(match[2]))
by_net=defaultdict(list)
for row in p['connections']:by_net[row['net_id']].append(row)
exports={};mapping=[]
def format_node(n,switch,pin_index=None):
 node=g.nodes[n];loc=dict(node.location);x=int(loc['xlow']);y=int(loc['ylow']);xh=int(loc['xhigh']);yh=int(loc['yhigh']);layer=int(loc.get('layer','0'));ptc=int(loc['ptc']);coord=f'({x},{y},{layer})';coord+=f' to ({xh},{yh},{layer})' if (x,y)!=(xh,yh) else '';kind=node.type;detail=''
 if kind in {'CHANX','CHANY'}:label='Track:'
 else:
  tid=grid[(x,y,layer)][0];io={k[0] for k in types[tid]['pins']}=={'io'};label='Pad:' if io else 'Pin:' if kind in {'OPIN','IPIN'} else 'Class:'
  if kind in {'OPIN','IPIN'} and not io:detail=' '+pin_names[tid][ptc]
 line=f'Node: {n} {kind} {coord} {label} {ptc}{detail} Switch: {switch}'
 if kind=='SINK':assert pin_index is not None;line+=f' Net_pin_index: {pin_index}'
 return line
for net,rows in sorted(by_net.items()):
 name=e['net_names'][str(net)];assert name in headers and 'global net' not in headers[name];adj=defaultdict(dict);sink_indices={};cohorts=defaultdict(list)
 for row in rows:cohorts[row['sink']].append(row)
 for sink,cohort in cohorts.items():
  indices=sorted(native_sink_indices[(name,sink)]);assert len(indices)==len(cohort)
  for row,index in zip(sorted(cohort,key=lambda r:r['connection_id']),indices):sink_indices[sink]=index;mapping.append({'connection_id':row['connection_id'],'frontend_net_id':net,'native_net_name':name,'sink':sink,'native_net_pin_index':index})
 for row in rows:
  for eid in row['physical_edge_ids']:
   edge=g.edges[eid];assert edge.sink not in adj[edge.source] or adj[edge.source][edge.sink]==edge.switch_id;adj[edge.source][edge.sink]=edge.switch_id
 root=rows[0]['source'];lines=[]
 def walk(node):
  if node not in adj:lines.append(format_node(node,-1,sink_indices[node]));return
  for child,switch in sorted(adj[node].items()):lines.append(format_node(node,switch));walk(child)
 walk(root);exports[name]=headers[name]+'\n\n'+'\n'.join(lines)+'\n\n'
# Every original net section is retained, including ignored global clock nets.
render=[parts[0]]
for chunk in parts[1:]:
 name=re.match(r'Net \d+ \((.*)\)',chunk.splitlines()[0])[1];render.append(exports.get(name,chunk))
assert all(sha(path)==h for path,h in inputs.items());out.mkdir();(out/'alu4.route').write_text(''.join(render));(out/'mapping.json').write_text(json.dumps(mapping)+'\n');(out/'source.py').write_text(Path(__file__).read_text());r={'input_sha256':inputs,'route_sha256':sha(out/'alu4.route'),'mapping_sha256':sha(out/'mapping.json'),'source_sha256':sha(out/'source.py'),'exported_nets':len(exports),'exported_connections':len(mapping),'preserved_template_net_sections':len(chunks)-len(exports),'full_wall_s':time.monotonic()-start,'scope':'traceback export of physical paths; same-class duplicate sink identity is deterministic CID/native-index ordinal; native reader/checker/resync/STA still required'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
