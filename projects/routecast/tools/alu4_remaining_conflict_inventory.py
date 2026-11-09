"""Inventory actual residual channel conflicts, without candidate-library assumptions."""
import json,time
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
start=time.monotonic()
out=Path('experiments/alu4_remaining_conflict_inventory_2026-10-05')
if out.exists():raise ValueError('fresh output required')
completion={'joint_prediction':'experiments/alu4_sequential_pin_round2_2026-10-05/prediction.json'}
files={'prediction':completion['joint_prediction'],'graph':'work/alu4_validation_capture_2026-10-05/rr_graph.xml','endpoints':'experiments/alu4_validation_capture_2026-10-05/endpoints.json'}
inputs={p:sha(p) for p in files.values()};g=read_rr_graph(files['graph']);pred=json.loads(Path(files['prediction']).read_text());checked=audit(g,json.loads(Path(files['endpoints']).read_text()),pred)
users=defaultdict(set);requests=defaultdict(list);per=[]
for r in pred['connections']:
 nodes={g.edges[e].sink for e in r['physical_edge_ids'] if g.nodes[g.edges[e].sink].type in {'CHANX','CHANY'}}
 for n in nodes:users[n].add(r['net_id']);requests[n].append(r['connection_id'])
 per.append((r,nodes))
conflicts={n for n,v in users.items() if len(v)>g.nodes[n].capacity}
resources=[{'rr_node':n,'capacity':g.nodes[n].capacity,'current_net_ids':sorted(users[n]),'connection_ids':sorted(requests[n]),'overuse':len(users[n])-g.nodes[n].capacity} for n in sorted(conflicts)]
selected=[{'cid':r['connection_id'],'net':r['net_id'],'overloaded_channels_on_path':sorted(nodes&conflicts)} for r,nodes in per if nodes&conflicts]
assert sum(r['overuse'] for r in resources)==8
assert all(sha(p)==h for p,h in inputs.items())
out.mkdir();(out/'source.py').write_text(Path(__file__).read_text())
for name,data in [('resources.json',resources),('requests.json',selected)]: (out/name).write_text(json.dumps(data,indent=2)+'\n')
receipt={'input_sha256':inputs,'overuse':8,'overloaded_channels':len(resources),'affected_connections':len(selected),'affected_nets':len({r['net'] for r in selected}),'physical_audit':checked,'full_wall_s':time.monotonic()-start,'source_sha256':sha(out/'source.py'),'artifacts_sha256':{n:sha(out/n) for n in ('resources.json','requests.json')}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
