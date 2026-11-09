"""Matched full/selective queries at fixed checkpoints of archived trunk construction."""
import json,time
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from weighted_pin_candidates import WeightedPins
from net_pressure_sketch import net_union
out=Path('experiments/frisc_target_pin_search_profile_2026-10-05')
if out.exists():raise ValueError('fresh output required')
start=time.monotonic();root=Path('experiments/frisc_shared_trunk_gated_candidate_2026-10-05');protocol=json.loads((root/'protocol.json').read_text());files={'prediction':next(p for p in protocol['input_sha256'] if 'prediction.json' in p),'graph':'work/frisc_graph_capture_2026-10-05/rr_graph.xml','paths':str(root/'candidate_paths.json')};inputs={p:sha(p) for p in files.values()};g=read_rr_graph(files['graph']);engine=WeightedPins(g);bg=json.loads(Path(files['prediction']).read_text());paths=json.loads(Path(files['paths']).read_text());old={r['connection_id']:r for r in bg['connections']};net=protocol['selected_net'];users,demand=net_union(g,bg);blocked={n for n,node in g.nodes.items() if node.type in {'CHANX','CHANY'} and demand.get(n,0)-int(n in users[net])>=node.capacity};span={};incoming=defaultdict(list)
for eid,edge in enumerate(g.edges):incoming[edge.sink].append(eid)
for n,node in g.nodes.items():
 loc=dict(node.location);span[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1 if node.type in {'CHANX','CHANY'} else 0
reports=[]
for index in (0,25,50,75,100,125,150,180):
 built={g.edges[e].sink for r in paths[:index] for e in r['physical_edge_ids']};parents={g.edges[e].sink:e for r in paths[:index] for e in r['physical_edge_ids']};forbidden={eid for n,parent in parents.items() for eid in incoming[n] if eid!=parent};row=old[paths[index]['connection_id']];w=engine.catalog.witness(row['source'],row['sink'],row['physical_edge_ids']);ptc=w['selected_ipin_ptc'];costs=[span[edge.sink]*(1+(0 if edge.sink in built else 10000)) for edge in g.edges];r={'index':index,'cid':row['connection_id']};results={}
 for label,target in (('full',None),('target',{ptc})):
  t=time.monotonic();result=engine.query(row['source'],row['sink'],w['selected_opin_ptc'],costs,blocked,forbidden,target_pins=target);r[label]={'query_s':time.monotonic()-t,'settled_nodes':result['settled_nodes'],'examined_edges':result['examined_edges']};results[label]=result
 assert results['full']['paths'][ptc]==results['target']['paths'][ptc]==paths[index]['physical_edge_ids'];assert results['full']['costs'][ptc]==results['target']['costs'][ptc];r['path_and_cost_exact']=True;reports.append(r);print(json.dumps(r),flush=True)
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'search.py').write_text(Path('tools/weighted_pin_candidates.py').read_text());receipt={'reports':reports,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'search_sha256':sha(out/'search.py'),'full_wall_s':time.monotonic()-start,'scope':'8 fixed real-query checkpoints, identical costs/blocked constraints and exact path/cost equality; concurrent host pilot timing is descriptive, excludes frontend/commit/STA, no end-to-end or hardware speed claim'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
