"""Freeze graph-bound drive points and same-phase native ready NET boxes, no labels."""
import json,struct,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_competitive_frontier_trial_v1_2026-10-20';D=E/'prince_ready_NET_geometry_v2_2026-10-20';H=E/'prince_cumulative_prefix_novelty_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);fp=H/'frozen_inputs.json';frozen=json.loads(fp.read_text());design=H/'ready_NET_geometry_attribution_design_v1.json';native=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route/route_common.h';sp=S/'protocol.json';staging=json.loads(sp.read_text());jobs={j['case']:j for j in staging['jobs']};bindings={str(p):sha(p) for p in [fp,design,native,sp,Path(__file__)]};(D/'protocol.json').write_text(json.dumps(dict(design=json.loads(design.read_text()),bindings=dict(bindings),epoch='post_route_accumulated_cost_and_timing_update__pre_dynamic_BB_update_and_pres_advance',containment='Inclusive bounds on direction-dependent drive point:DEC_DIR high/high,otherwise low/low,with native layer. Not segment overlap.'),indent=2)+'\n');graphs={};rows=[]
 for row in frozen['rows']:
  c=row['case']
  if row['status']!='CUMULATIVE_INPUTS_FROZEN_NO_LABELS':rows.append(dict(case=c,status=row['status']));continue
  width=c.split('/')[0];src=S/c/'capture';t=row['ready_iteration'];rp=src/'receipt.json';receipt=json.loads(rp.read_text());identity=(src/'identity.txt').read_text().splitlines();graph=E/'prince_native_cohort_v1_2026-10-20'/width/'source/rr_graph.xml';mapping=E/'prince_resident_consumer_v1_2026-10-20'/c/'NET_mapping.json';mp=json.loads(mapping.read_text());assert all(sha(src/name)==receipt['files'][str(src/name)] for name in ['identity.txt','NET_mapping.tsv','queries.tsv.connections.tsv']);assert all(sha(src/name)==sha(jobs[c+'/capture']['staging'][name])==staging['bindings'][jobs[c+'/capture']['staging'][name]] for name in ['design.net','design.place']);assert identity[:3]==[sha(graph),sha(src/'design.net'),sha(src/'design.place')];expected=''.join(f"{x['native_NET_id']}\t{x['endpoint_NET_id']}\t{int(x['ignored_global'])}\t{x['name']}\n" for x in sorted(mp,key=lambda x:x['native_NET_id']));assert (src/'NET_mapping.tsv').read_text()==expected
  if width not in graphs:
   points={}
   for event,node in ET.iterparse(graph,events=['end']):
    if node.tag!='node':continue
    a=node.attrib
    if a.get('type') in ['CHANX','CHANY'] and int(a['capacity'])>0:
     loc=node.find('loc').attrib;direction=a.get('direction','NO_DIR');high=direction=='DEC_DIR';point=[int(loc['xhigh' if high else 'xlow']),int(loc['yhigh' if high else 'ylow']),int(loc.get('layer',0))];points[int(a['id'])]=dict(id=int(a['id']),kind=a['type'],direction=direction,capacity=int(a['capacity']),drive_point=point)
    node.clear()
   dp=E/'prince_quality_domains_v1_2026-10-20'/width/'resources.jsonl';assert set(points)=={x['id'] for x in map(json.loads,dp.open())};folder=D/width;folder.mkdir();path=folder/'drive_points.jsonl';path.write_text(''.join(json.dumps(points[n],separators=(',',':'))+'\n' for n in sorted(points)));graphs[width]=path
   for p in [graph,dp,path]:bindings[str(p)]=sha(p)
  boxp=src/'boundary'/f'boxes_{t}.bin';assert sha(boxp)==receipt['files'][str(boxp)] and sha(boxp)==sha(src/'callback.tsv.ready_boxes.bin');raw=boxp.read_bytes();assert raw[:8]==b'RCBOX001';i,count=struct.unpack_from('<QQ',raw,8);assert i==t and len(raw)==24+count*32;boxes={n:list(b) for n,*b in struct.iter_unpack('<Q6i',raw[24:])};assert len(boxes)==count==len(mp) and set(boxes)=={x['native_NET_id'] for x in mp};active=set()
  for line in (src/'queries.tsv.connections.tsv').open():
   phase,ident,net,pin,sink,size=map(int,line.split())
   if phase==t:active.add(net)
  folder=D/c;folder.mkdir(parents=True);path=folder/'NET_boxes.jsonl'
  with path.open('x') as f:
   for x in sorted(mp,key=lambda x:x['native_NET_id']):
    net=x['native_NET_id'];b=boxes[net];assert all(b[k]<=b[k+1] for k in [0,2,4]);f.write(json.dumps(dict(native_NET=net,endpoint_NET=x['endpoint_NET_id'],name=x['name'],ignored_global=x['ignored_global'],box=b,ready_connection_active=net in active),separators=(',',':'))+'\n')
  for p in [rp,src/'identity.txt',src/'NET_mapping.tsv',src/'design.net',src/'design.place',mapping,boxp,src/'queries.tsv.connections.tsv',path]:bindings[str(p)]=sha(p)
  rows.append(dict(case=c,status='READY_GEOMETRY_FROZEN_NO_LABELS',ready_iteration=t,points=str(graphs[width]),NET_boxes=str(path),NETs=len(boxes),ready_active_NETs=len(active)));print('READY_GEOMETRY_FROZEN',c,len(boxes),len(active),flush=True)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items());(D/'frozen_inputs.json').write_text(json.dumps(dict(status='GRAPH_AND_READY_NET_GEOMETRY_FROZEN',rows=rows,bindings=bindings,final_labels_read=False),indent=2)+'\n')
if __name__=='__main__':main()
