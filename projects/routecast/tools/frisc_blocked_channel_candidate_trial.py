import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from weighted_pin_candidates import WeightedPins
from net_pressure_sketch import net_union
out=Path('experiments/frisc_blocked_channel_candidates_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files={'graph':'work/frisc_graph_capture_2026-10-05/rr_graph.xml','prediction':'experiments/frisc_sequential_pin_compatible_round4_2026-10-05/prediction.json','rows':'experiments/frisc_packed_pin_witness_2026-10-05/rows.json','bounds':'experiments/frisc_residual_candidate_bounds_2026-10-05/request_mandatory_channels.json'}
inputs={p:sha(p) for p in files.values()};start=time.monotonic();g=read_rr_graph(files['graph']);engine=WeightedPins(g);pred=json.loads(Path(files['prediction']).read_text());users,demand=net_union(g,pred);rows={r['connection_id']:r for r in json.loads(Path(files['rows']).read_text())};selected=[r for r in json.loads(Path(files['bounds']).read_text()) if 31148 in r['mandatory_channels']];assert len(selected)==2;results={};reports=[]
for r in selected:
 cid=r['cid'];net=r['net'];row=rows[cid];w=row['path_pin_witness'];cost={}
 for n,node in g.nodes.items():
  value=0
  if node.type in {'CHANX','CHANY'} and node.capacity>0:
   loc=dict(node.location);value=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1;c=node.capacity;d=demand.get(n,0)-int(n in users[net]);value+=(256*max(0,d-c+1)+c-1)//c
  cost[n]=value
 t=time.monotonic();result=engine.query(w['source_class'],w['sink_class'],row['packed_source']['physical_pin_ptc'],[cost[e.sink] for e in g.edges],{31148})
 for ptc,path in result['paths'].items():
  assert all(g.edges[e].sink!=31148 for e in path);witness=engine.catalog.witness(w['source_class'],w['sink_class'],path);assert witness['selected_ipin_ptc']==ptc
 results[cid]=result;reports.append({'cid':cid,'net':net,'reachable_pins_avoiding_channel':len(result['paths']),'query_s':time.monotonic()-t})
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'paths.json').write_text(json.dumps(results)+'\n');(out/'source.py').write_text(Path(__file__).read_text());receipt={'blocked_channel':31148,'reports':reports,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'search_sha256':sha('tools/weighted_pin_candidates.py'),'paths_sha256':sha(out/'paths.json'),'full_wall_s':time.monotonic()-start,'scope':'new directed physical candidates avoiding one mandatory channel, fixed nominal source pin; no assignment/tree compatibility or committed repair'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
