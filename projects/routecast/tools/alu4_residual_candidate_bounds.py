"""Necessary unique-net demand lower bounds within the explicit candidate library."""
import json,time
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
out=Path('experiments/alu4_residual_candidate_bounds_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files={'prediction':'experiments/alu4_full_weighted_pin_commit_2026-10-05/prediction.json','paths':'experiments/alu4_full_weighted_pin_trial_2026-10-05/paths.json','endpoints':'experiments/alu4_validation_capture_2026-10-05/endpoints.json','graph':'work/alu4_validation_capture_2026-10-05/rr_graph.xml'}
inputs={p:sha(p) for p in files.values()};start=time.monotonic();g=read_rr_graph(files['graph']);pred=json.loads(Path(files['prediction']).read_text());e=json.loads(Path(files['endpoints']).read_text());audit(g,e,pred);paths=json.loads(Path(files['paths']).read_text());forced=defaultdict(set);users=defaultdict(set);per_request=[]
for row in pred['connections']:
 cid=str(row['connection_id']);net=row['net_id']
 def channels(path):return {g.edges[eid].sink for eid in path if g.nodes[g.edges[eid].sink].type in {'CHANX','CHANY'}}
 actual=channels(row['physical_edge_ids'])
 for n in actual:users[n].add(net)
 options=list(paths[cid]['paths'].values()) if cid in paths else [row['physical_edge_ids']]
 mandatory=None
 for path in options:
  nodes=channels(path);mandatory=nodes if mandatory is None else mandatory&nodes
 forced[net].update(mandatory);per_request.append({'cid':int(cid),'net':net,'candidate_count':len(options),'mandatory_channels':sorted(mandatory)})
mandatory_users=defaultdict(set)
for net,nodes in forced.items():
 for n in nodes:mandatory_users[n].add(net)
records=[]
for n,nets in sorted(users.items()):
 cap=g.nodes[n].capacity
 if len(nets)<=cap:continue
 required=mandatory_users[n];assert required<=nets
 records.append({'rr_node':n,'capacity':cap,'current_net_ids':sorted(nets),'mandatory_net_ids':sorted(required),'current_overuse':len(nets)-cap,'library_lower_bound_overuse':max(0,len(required)-cap)})
# Include lower bounds on resources not currently overloaded as a consistency check.
assert all(len(nets)<=len(users[n]) for n,nets in mandatory_users.items())
current=sum(r['current_overuse'] for r in records);lower=sum(max(0,len(v)-g.nodes[n].capacity) for n,v in mandatory_users.items());assert current==617 and lower<=current
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'resources.json').write_text(json.dumps(records,indent=2)+'\n');(out/'request_mandatory_channels.json').write_text(json.dumps(per_request)+'\n');receipt={'current_overuse':current,'overloaded_channels':len(records),'explicit_library_necessary_overuse_lower_bound':lower,'forced_overloaded_channels':sum(r['library_lower_bound_overuse']>0 for r in records),'full_wall_s':time.monotonic()-start,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'artifacts_sha256':{n:sha(out/n) for n in ('resources.json','request_mandatory_channels.json')},'scope':'mandatory-channel intersection across all supplied paths, unselected requests fixed; positive bound proves this library insufficient, zero bound does not prove feasible joint assignment or all RR infeasibility'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
