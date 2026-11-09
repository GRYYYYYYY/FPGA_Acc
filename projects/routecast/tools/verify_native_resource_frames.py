import json,math,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_resource_frames_2026-10-06';work=root/'work/native_candidate_resource_frames_2026-10-06';receipt=json.loads((out/'receipt.json').read_text());results=[];bindings={}
for row,count in zip(receipt['results'],(129,516)):
 cmd=row['command'];graph=Path(cmd[cmd.index('--read_rr_graph')+1]);nodes={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':nodes[int(e.get('id'))]=(e.get('type'),int(e.get('capacity')))
  if (e.tag,parent) in (('node','rr_nodes'),('edge','rr_edges'),('switch','switches')):stack[-2].remove(e);e.clear()
  stack.pop()
 cwd=work/row['design']
 for step in range(4):
  p=cwd/f'state_{step}.resources.tsv';lines=p.read_text().splitlines();resources={int(x[0]):(int(x[1]),float(x[2])) for line in lines[2:] if (x:=line.split('\t'))};assert set(resources)==set(nodes)
  a=audit(graph,cwd/f'state_{step}.route');assert len(a['connections'])==count and a['overflow_units']==0;native_demand={n:occ for n,(occ,cost) in resources.items() if occ};routed={int(n):occ for n,occ in a['node_occupancy'].items()};residual={}
  for n,(occ,cost) in resources.items():
   assert 0<=occ<=nodes[n][1] and math.isfinite(cost) and cost>=1
   assert occ>=routed.get(n,0)
   if occ>routed.get(n,0):residual[n]=occ-routed.get(n,0);assert nodes[n][0]=='OPIN'
  results.append({'design':row['design'],'step':step,'node_count':len(nodes),'routed_occupied_nodes':len(routed),'native_occupied_nodes':len(native_demand),'local_opin_residual_units':sum(residual.values()),'resource_sha256':sha(p)});bindings[str(p)]=sha(p)
 bindings[str(graph)]=sha(graph)
(out/'resource_verification.json').write_text(json.dumps({'frames':results,'inputs_sha256':bindings,'scope':'Native occupancy vs independent per-NET printed route union, all residual demand restricted to local OPIN reservations; original RR capacities and finite accumulated costs checked. Not yet per-NET-excluded RC context or dynamic RC score.'},indent=2)+'\n');print('verified',len(results),'resource frames')
