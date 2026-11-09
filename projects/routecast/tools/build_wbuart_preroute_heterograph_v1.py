"""Label-free NET/RR/tile relations from audited pre-route endpoint inputs only."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_preroute_heterograph_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def write_lines(p,rows):
 with p.open('x') as f:
  for r in rows:f.write(json.dumps(r,separators=(',',':'))+'\n')
def main():
 D.mkdir(exist_ok=False);inventory=E/'wbuart_uniform_pool_forecast_v1_2026-10-20/forecasts_frozen.json';items={r['case']:r['endpoint'] for r in read(inventory)['rows']};assert len(items)==9
 manifest={'status':'SOURCE_ONLY_HETEROGRAPH_INPUTS_FROZEN','cases':items,'input_roles':['RR XML','packed-netlist/placement pre-route endpoint artifacts'],'features':'RR original ID/type/direction/capacity/segment/location/R/C; directed physical edgeID/switch; interval tile incidence; NET fanout/endpoint bbox; CID-preserving source/sink incidence. No candidate paths, source/target route, target occupancy, labels, timing criticalities, learned normalization or weights.','scope':'Input representation only, not a predictor, learned baseline or family admission. No upstream code imported.','bindings':{str(Path(__file__)):sha(__file__),str(inventory):sha(inventory)}};mp=D/'manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');graphs={};bindings={str(mp):sha(mp)};rows=[]
 for case,endpoint in sorted(items.items()):
  ep=read(endpoint);g=Path(ep['inputs']['graph']['path']);digest=sha(g);assert digest==ep['graph_sha256']==ep['inputs']['graph']['sha256']
  for role in ['net','place']:assert sha(ep['inputs'][role]['path'])==ep['inputs'][role]['sha256']
  if digest not in graphs:
   directory=D/'graphs'/digest;directory.mkdir(parents=True);root=ET.parse(g).getroot();nodes={};tile_links=[]
   for n in root.find('rr_nodes'):
    loc={k:int(v) if k!='side' else v for k,v in n.find('loc').attrib.items()};timing=n.find('timing');segment=n.find('segment');node={'id':int(n.get('id')),'type':n.get('type'),'direction':n.get('direction'),'capacity':int(n.get('capacity')),'loc':loc,'segment_id':int(segment.get('segment_id')) if segment is not None else None,'timing':dict(timing.attrib) if timing is not None else {}};nodes[node['id']]=node
    for x in range(loc['xlow'],loc['xhigh']+1):
     for y in range(loc['ylow'],loc['yhigh']+1):tile_links.append({'RR':node['id'],'tile':[x,y]})
   edges=[{'edge_id':i,'source':int(e.get('src_node')),'sink':int(e.get('sink_node')),'switch_id':int(e.get('switch_id'))} for i,e in enumerate(root.find('rr_edges'))]
   assert all(e['source'] in nodes and e['sink'] in nodes for e in edges)
   write_lines(directory/'RR_nodes.jsonl',[nodes[n] for n in sorted(nodes)]);write_lines(directory/'physical_edges.jsonl',edges);write_lines(directory/'RR_tile_incidence.jsonl',tile_links);graphs[digest]={'directory':str(directory),'nodes':nodes,'RR_nodes':len(nodes),'physical_edges':len(edges),'RR_tile_links':len(tile_links),'graph':str(g)}
   for p in directory.iterdir():bindings[str(p)]=sha(p)
   bindings[str(g)]=digest;del root,edges,tile_links
  info=graphs[digest];nodes=info['nodes'];nets=defaultdict(list);cids=set()
  for q in ep['connections']:
   assert q['connection_id'] not in cids;cids.add(q['connection_id']);assert nodes[q['source']]['type']=='SOURCE' and nodes[q['sink']]['type']=='SINK';nets[q['net_id']].append(q)
  net_rows=[];incidences=[]
  for net,queries in sorted(nets.items()):
   assert len({q['source'] for q in queries})==1;points=[nodes[q[key]]['loc'] for q in queries for key in ['source','sink']];bbox=[min(p['xlow'] for p in points),min(p['ylow'] for p in points),max(p['xhigh'] for p in points),max(p['yhigh'] for p in points)];net_rows.append({'net_id':net,'name':ep['net_names'][str(net)],'fanout':len(queries),'source_RR':queries[0]['source'],'endpoint_bbox':bbox})
   for q in queries:incidences.append({k:q[k] for k in ['connection_id','full_connection_id','net_id','source','sink']})
  directory=D/case;directory.mkdir(parents=True);write_lines(directory/'NET_features.jsonl',net_rows);write_lines(directory/'NET_RR_incidence.jsonl',incidences)
  for p in directory.iterdir():bindings[str(p)]=sha(p)
  for path in [Path(endpoint),Path(ep['inputs']['net']['path']),Path(ep['inputs']['place']['path'])]:bindings[str(path)]=sha(path)
  rows.append({'case':case,'endpoint':endpoint,'graph_sha256':digest,'NETs':len(nets),'connections':len(cids),'directory':str(directory)});print('PREROUTE_HETEROGRAPH',case,len(nets),len(cids),flush=True)
 graph_rows=[{k:v for k,v in g.items() if k!='nodes'} for g in graphs.values()];(D/'verification.json').write_text(json.dumps({'status':'ALL9_INPUT_ONLY_NET_RR_TILE_GRAPHS_PRODUCED','rows':rows,'graphs':graph_rows,'target_payloads_read':False,'candidate_payloads_read':False,'independent_audit_pending':True,'bindings':bindings},indent=2)+'\n')
if __name__=='__main__':main()
