"""Evaluator-only native selected-net occupancy; fixed pilot, all metrics."""
import json,shutil
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from native_node_labels import node_labels
from pin_template_trial import spatial
from prediction_metrics import compare
from audit_native_route import NET,NODE
parent=Path('experiments/clma_tree_reuse_pilot_2026-10-04');out=Path('experiments/clma_tree_reuse_evaluation_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((parent/'protocol.json').read_text());receipt=json.loads((parent/'receipt.json').read_text());assert receipt['protocol_sha256']==sha(parent/'protocol.json');selected=set(p['selected_nets']);cap=json.loads(Path('experiments/clma_base_echo_2026-10-04/protocol.json').read_text())
inputs={'graph':p['inputs']['graph'],'route':cap['inputs']['route'],'place':cap['inputs']['place']}
for name,f in [('control','control_prediction.json'),('reuse','prediction.json'),('endpoints','endpoints.json')]:
 path=parent/f;assert receipt['outputs'][f]==sha(path);inputs[name]={'path':str(path.resolve()),'sha256':sha(path)}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'inputs':inputs,'scope':'selected87net pilot, native filtered labels evaluator only; no full-design or native QoR inference','metrics':['spatial/resource Spearman and top20/5percent precision/MAE','overflowunits','connection touches/net union/sharing'],'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
g=read_rr_graph(inputs['graph']['path']);filtered=[];net=None;native_endpoints=Counter();source=None
for line in Path(inputs['route']['path']).read_text().splitlines():
 m=NET.match(line)
 if m:net=int(m[1]);source=None
 if net is None or net in selected:filtered.append(line)
 m=NODE.match(line)
 if m and net in selected:
  if m[2]=='SOURCE':source=int(m[1])
  if m[2]=='SINK':native_endpoints[(net,source,int(m[1]))]+=1
endpoint_rows=json.loads(Path(inputs['endpoints']['path']).read_text())['connections'];assert native_endpoints==Counter((r['net_id'],r['source'],r['sink']) for r in endpoint_rows)
filtered_path=out/'native_selected_route.txt';filtered_path.write_text('\n'.join(filtered)+'\n');truth=node_labels(g,filtered_path,inputs['place']['sha256']);resources=[n for n,v in g.nodes.items() if v.type in {'CHANX','CHANY'} and v.capacity];reports={}
for name in ('control','reuse'):
 pred=json.loads(Path(inputs[name]['path']).read_text());assert pred['physical_graph_sha256']==g.sha256;values=pred['node_occupancy'];connection=0
 for r in pred['connections']:connection+=sum(g.nodes[g.edges[e].sink].type in {'CHANX','CHANY'} for e in r['physical_edge_ids'])
 union=sum(values.get(str(n),0) for n in resources)
 reports[name]={'resource':compare({str(n):values.get(str(n),0)/g.nodes[n].capacity for n in resources},{str(n):truth.get(str(n),0)/g.nodes[n].capacity for n in resources},max(1,len(resources)//20)),'spatial':compare(spatial(g,values),spatial(g,truth),20),'overflow_units':sum(max(0,v-g.nodes[int(n)].capacity) for n,v in values.items()),'connection_channel_touches':connection,'net_channel_touches':union,'sharing_saved_fraction':1-union/connection}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'exact_native_pilot_endpoints':True,'inputs_unchanged':True,'native_net_channel_touches':sum(truth.get(str(n),0) for n in resources),'filtered_route_sha256':sha(filtered_path),'reports':reports},indent=2)+'\n');print(json.dumps(reports),flush=True)
