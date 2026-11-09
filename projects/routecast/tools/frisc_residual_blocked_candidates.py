"""Frozen-background candidate extension for every current residual-conflict request."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from weighted_pin_candidates import WeightedPins
from net_pressure_sketch import net_union
from net_union_commit_gate import check
start=time.monotonic();out=Path('experiments/frisc_residual_blocked_candidates_2026-10-05')
if out.exists():raise ValueError('fresh output required')
inventory=Path('experiments/frisc_remaining_conflict_inventory_2026-10-05');inv=json.loads((inventory/'receipt.json').read_text())
files={'prediction':next(p for p in inv['input_sha256'] if p.endswith('.json') and 'prediction_' in p),'graph':'work/frisc_graph_capture_2026-10-05/rr_graph.xml','requests':str(inventory/'requests.json')}
inputs={p:sha(p) for p in files.values()};g=read_rr_graph(files['graph']);engine=WeightedPins(g);pred=json.loads(Path(files['prediction']).read_text());rows={r['connection_id']:r for r in pred['connections']};users,demand=net_union(g,pred);selected=json.loads(Path(files['requests']).read_text());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());reports=[];results={}
for i,request in enumerate(selected):
 cid=request['cid'];old=rows[cid];w=engine.catalog.witness(old['source'],old['sink'],old['physical_edge_ids']);net=old['net_id'];cost={}
 for n,node in g.nodes.items():
  value=0
  if node.type in {'CHANX','CHANY'} and node.capacity>0:
   loc=dict(node.location);value=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1;c=node.capacity;d=demand.get(n,0)-int(n in users[net]);value+=(256*max(0,d-c+1)+c-1)//c
  cost[n]=value
 t=time.monotonic();blocked=set(request['overloaded_channels_on_path']);result=engine.query(old['source'],old['sink'],w['selected_opin_ptc'],[cost[e.sink] for e in g.edges],blocked);path=result['paths'].get(w['selected_ipin_ptc']);report={**request,'query_s':time.monotonic()-t,'same_pin_reachable':path is not None,'selected_ipin_ptc':w['selected_ipin_ptc'],'selected_opin_ptc':w['selected_opin_ptc']}
 if path is not None:
  witness=engine.catalog.witness(old['source'],old['sink'],path);assert witness['selected_opin_ptc']==w['selected_opin_ptc'] and witness['selected_ipin_ptc']==w['selected_ipin_ptc'];assert all(g.edges[e].sink not in blocked for e in path)
  new={**old,'physical_edge_ids':path,'method':'residual_blocked_repair'};gate=check(g,pred,[new]);report['whole_net_accepted']=gate['accepted'];report['rejected_nets']=gate['rejected_nets'];results[cid]=new
 reports.append(report);print(json.dumps({'index':i+1,'total':len(selected),'cid':cid,'reachable':report['same_pin_reachable'],'tree_accepted':report.get('whole_net_accepted')}),flush=True)
 (out/'progress.json').write_text(json.dumps(reports)+'\n')
assert all(sha(p)==h for p,h in inputs.items());(out/'replacements.json').write_text(json.dumps(results)+'\n');receipt={'input_sha256':inputs,'reports':reports,'source_sha256':sha(out/'source.py'),'search_sha256':sha('tools/weighted_pin_candidates.py'),'replacements_sha256':sha(out/'replacements.json'),'full_wall_s':time.monotonic()-start,'scope':'135 frozen-background queries; fixed existing physical pins, block overloaded channels on each original path; individual whole-net compatibility only, no joint commit'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'completed':len(reports),'reachable':sum(r['same_pin_reachable'] for r in reports),'tree_accepted':sum(r.get('whole_net_accepted',False) for r in reports),'full_wall_s':receipt['full_wall_s']}),flush=True)
