"""Retrospective full-design composition, fixed preselected87 nets only."""
import json,shutil
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from rr_occupancy import Occupancy
from connection_golden import Result
from physical_prediction_audit import audit
from native_node_labels import node_labels
from pin_template_trial import spatial
from prediction_metrics import compare
out=Path('experiments/clma_tree_pilot_composition_2026-10-04')
if out.exists():raise ValueError('fresh output required')
parent=Path('experiments/clma_tree_reuse_pilot_2026-10-04');proto=json.loads((parent/'protocol.json').read_text());receipt=json.loads((parent/'receipt.json').read_text());cap=json.loads(Path('experiments/clma_base_echo_2026-10-04/protocol.json').read_text());paths={'control':Path(proto['inputs']['control']['path']),'tree_pilot':parent/'prediction.json','endpoints':Path(proto['inputs']['endpoints']['path']),'graph':Path(proto['inputs']['graph']['path']),'route':Path(cap['inputs']['route']['path']),'place':Path(cap['inputs']['place']['path'])}
assert receipt['outputs']['prediction.json']==sha(paths['tree_pilot'])
inputs={k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in paths.items()};out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'inputs':inputs,'scope':'retrospective fixed87net pilot composition, other nets unchanged, same frozen graph/base cost; no full-tree/crossfamily/nativeQoR inference','selected_nets':proto['selected_nets'],'metrics':'same prior spatialtop20/resourcetop5percent/MAE/overflow, report all','source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
g=read_rr_graph(paths['graph']);e=json.loads(paths['endpoints'].read_text());control=json.loads(paths['control'].read_text());tree=json.loads(paths['tree_pilot'].read_text());replacements={r['connection_id']:r for r in tree['connections']};rows=[];ledger=Occupancy(g)
for old in control['connections']:
 row=replacements.get(old['connection_id'],old)
 assert all(row[k]==old[k] for k in ('connection_id','net_id','source','sink'))
 assert ledger.update(row['connection_id'],1,row['net_id'],row['source'],row['sink'],row['physical_edge_ids'])==Result.COMMITTED
 rows.append(row)
assert len(replacements)==5734;pred={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'requested':len(rows),'completed':len(rows),'methods':dict(Counter(r['method'] for r in rows))};checked=audit(g,e,pred);(out/'prediction.json').write_text(json.dumps(pred)+'\n')
truth=node_labels(g,paths['route'],inputs['place']['sha256']);resources=[n for n,v in g.nodes.items() if v.type in {'CHANX','CHANY'} and v.capacity];reports={}
for name,prediction in [('control',control),('composition',pred)]:
 values=prediction['node_occupancy'];reports[name]={'spatial':compare(spatial(g,values),spatial(g,truth),20),'resource':compare({str(n):values.get(str(n),0)/g.nodes[n].capacity for n in resources},{str(n):truth.get(str(n),0)/g.nodes[n].capacity for n in resources},max(1,len(resources)//20)),'overflow_units':sum(max(0,v-g.nodes[int(n)].capacity) for n,v in values.items()),'net_channel_touches':sum(values.get(str(n),0) for n in resources)}
firstsink=[];oldmap={r['connection_id']:r for r in control['connections']}
for net in proto['selected_nets']:
 rs=[r for r in tree['connections'] if r['net_id']==net];r=min(rs,key=lambda r:r['sink']);assert r['physical_edge_ids']==oldmap[r['connection_id']]['physical_edge_ids'];firstsink.append(net)
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'audit':checked,'first_sink_paths_exact_control_nets':len(firstsink),'inputs_unchanged':True,'reports':reports,'prediction_sha256':sha(out/'prediction.json')},indent=2)+'\n');print(json.dumps(reports),flush=True)
