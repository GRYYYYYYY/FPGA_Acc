"""Independent XML stream and direct endpoint reference of every graph relation."""
import json,xml.etree.ElementTree as ET,itertools
from pathlib import Path
from collections import defaultdict
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_preroute_heterograph_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def lines(p):
 with Path(p).open() as f:
  for line in f:yield json.loads(line)
def main():
 p=D/'verification.json';v=read(p);assert len(v['rows'])==9 and len(v['graphs'])==3 and not v['target_payloads_read'] and not v['candidate_payloads_read'];assert all(sha(name)==h for name,h in v['bindings'].items());graphs={};edge_total=0;tile_total=0;net_total=0;cid_total=0
 for g in v['graphs']:
  directory=Path(g['directory']);nodes={};edges=iter(lines(directory/'physical_edges.jsonl'));index=0
  for event,element in ET.iterparse(g['graph'],events=['end']):
   if element.tag=='node':
    node=int(element.get('id'));assert node not in nodes;nodes[node]={'attributes':dict(element.attrib),'loc':dict(element.find('loc').attrib),'timing':dict(element.find('timing').attrib) if element.find('timing') is not None else {},'segment':dict(element.find('segment').attrib) if element.find('segment') is not None else None};element.clear()
   elif element.tag=='edge':
    expected={'edge_id':index,'source':int(element.get('src_node')),'sink':int(element.get('sink_node')),'switch_id':int(element.get('switch_id'))};assert next(edges)==expected;index+=1;element.clear()
  assert next(edges,None) is None and index==g['physical_edges'];edge_total+=index;stored=list(lines(directory/'RR_nodes.jsonl'));assert len(stored)==len(nodes)==g['RR_nodes'] and len({n['id'] for n in stored})==len(nodes)
  expected_tiles=set()
  for n in stored:
   ref=nodes[n['id']];a=ref['attributes'];assert n['type']==a['type'] and n['direction']==a.get('direction') and n['capacity']==int(a['capacity']) and n['timing']==ref['timing'];assert n['segment_id']==(int(ref['segment']['segment_id']) if ref['segment'] is not None else None);assert n['loc']=={k:(value if k=='side' else int(value)) for k,value in ref['loc'].items()}
   loc=ref['loc']
   for x,y in itertools.product(range(int(loc['xlow']),int(loc['xhigh'])+1),range(int(loc['ylow']),int(loc['yhigh'])+1)):expected_tiles.add((n['id'],x,y))
  actual=[(r['RR'],*r['tile']) for r in lines(directory/'RR_tile_incidence.jsonl')];assert len(actual)==len(set(actual))==g['RR_tile_links'] and set(actual)==expected_tiles;tile_total+=len(actual);graphs[directory.name]=nodes
 for row in v['rows']:
  ep=read(row['endpoint']);nodes=graphs[row['graph_sha256']];directory=Path(row['directory']);actual=list(lines(directory/'NET_RR_incidence.jsonl'));expected=[{k:q[k] for k in ['connection_id','full_connection_id','net_id','source','sink']} for q in ep['connections']];assert sorted(actual,key=lambda q:q['connection_id'])==sorted(expected,key=lambda q:q['connection_id']);assert len(actual)==row['connections'];nets=defaultdict(list)
  for q in expected:nets[q['net_id']].append(q)
  features=list(lines(directory/'NET_features.jsonl'));assert len(features)==len(nets)==row['NETs'];assert len({n['net_id'] for n in features})==len(nets)
  for n in features:
   qs=nets[n['net_id']];assert n['fanout']==len(qs) and n['name']==ep['net_names'][str(n['net_id'])] and {q['source'] for q in qs}=={n['source_RR']};xs=[];ys=[]
   for q in qs:
    for key,kind in [('source','SOURCE'),('sink','SINK')]:
     ref=nodes[q[key]];assert ref['attributes']['type']==kind;xs.extend([int(ref['loc']['xlow']),int(ref['loc']['xhigh'])]);ys.extend([int(ref['loc']['ylow']),int(ref['loc']['yhigh'])])
   assert n['endpoint_bbox']==[min(xs),min(ys),max(xs),max(ys)]
  net_total+=len(features);cid_total+=len(actual);print('HETEROGRAPH_INDEPENDENT_PASS',row['case'],flush=True)
 out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL9_PREROUTE_RELATIONS_AND3_ORIGINAL_RR_GRAPHS_INDEPENDENTLY_VERIFIED','NET_rows':net_total,'connection_incidence_rows':cid_total,'physical_edges':edge_total,'RR_tile_links':tile_total,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Input relations only. No learned predictor, target labels/candidate generation, cross-family independence or quality/utility gain.'},indent=2)+'\n');print('ALL_HETEROGRAPH_INPUTS_VERIFIED',net_total,cid_total,edge_total,tile_total)
if __name__=='__main__':main()
