import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from weighted_pin_candidates import WeightedPins
from costed_pin_assignment import assign_costed
from net_pressure_sketch import net_union
out=Path('experiments/alu4_weighted_pin_trial_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files={'rows':'experiments/alu4_packed_pin_witness_2026-10-05/rows.json','background':'experiments/alu4_transfer_2026-10-05/prediction.json','equivalence':'experiments/alu4_full_pin_equivalence_audit_2026-10-05/receipt.json','graph':'work/alu4_validation_capture_2026-10-05/rr_graph.xml'}
inputs={p:sha(p) for p in files.values()};start=time.monotonic();g=read_rr_graph(files['graph']);engine=WeightedPins(g);bg=json.loads(Path(files['background']).read_text());users,demand=net_union(g,bg);eq=json.loads(Path(files['equivalence']).read_text());selected={r['cid'] for r in eq['checks'] if r['sink_class']==7653};rows=[r for r in json.loads(Path(files['rows']).read_text()) if r['connection_id'] in selected]
base={}
for n,node in g.nodes.items():
 if node.type in {'CHANX','CHANY'}:
  loc=dict(node.location);base[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1
 else:base[n]=0
out.mkdir();(out/'protocol.json').write_text(json.dumps({'input_sha256':inputs,'sink_class':7653,'alpha':256,'policy':'fixed nominal source; frozen own-net-excluded channel pressure, min supplied-cost matching; no native label input','source_sha256':sha(__file__)},indent=2)+'\n');results={};costs={};t=time.monotonic()
for r in rows:
 cid=r['connection_id'];net=r['net_id'];w=r['path_pin_witness'];q=time.monotonic();nodecost={}
 for n,node in g.nodes.items():
  d=demand.get(n,0)-int(n in users[net]);penalty=(256*max(0,d-node.capacity+1)+node.capacity-1)//node.capacity if node.type in {'CHANX','CHANY'} and node.capacity>0 else 0
  nodecost[n]=base[n]+penalty
 arc_costs=tuple(nodecost[e.sink] for e in g.edges);result=engine.query(w['source_class'],w['sink_class'],r['packed_source']['physical_pin_ptc'],arc_costs)
 assert len(result['paths'])==40
 results[cid]=result;costs[cid]={(w['sink_class'],p):value for p,value in result['costs'].items()}
 print(json.dumps({'cid':cid,'candidates':len(result['paths']),'wall_s':time.monotonic()-q}),flush=True)
query_wall=time.monotonic()-t;t=time.monotonic();assignment=assign_costed(costs);solver_wall=time.monotonic()-t;assert assignment['status']=='matched';assert all(sha(p)==h for p,h in inputs.items())
(out/'paths.json').write_text(json.dumps(results)+'\n');(out/'assignment.json').write_text(json.dumps(assignment)+'\n');(out/'source').mkdir()
for name in ('alu4_weighted_pin_trial.py','weighted_pin_candidates.py','reachable_pin_candidates.py','costed_pin_assignment.py','pin_assignment.py','net_pressure_sketch.py'):(out/'source'/name).write_text(Path('tools',name).read_text())
receipt={'requests':len(rows),'candidates':sum(len(r['paths']) for r in results.values()),'alpha':256,'query_wall_s':query_wall,'solver_wall_s':solver_wall,'full_wall_s':time.monotonic()-start,'optimal_supplied_cost':assignment['total_cost'],'input_sha256':inputs,'source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')},'artifact_sha256':{n:sha(out/n) for n in ('paths.json','assignment.json')},'scope':'single class fixed-source-pin weighted path candidates, frozen own-net-excluded baseline pressure; no joint tree or native QoR proof'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
