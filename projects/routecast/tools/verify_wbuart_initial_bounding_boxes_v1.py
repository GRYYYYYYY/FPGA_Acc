"""Expat graph parsing and independently reconstructed point-terminal boxes."""
import json,hashlib,xml.parsers.expat
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_initial_bbox_diagnosis_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'verification.json';v=read(p);assert all(sha(n)==h for n,h in v['bindings'].items());graphs={};rows=[]
 for c in v['rows']:
  g=c['graph']
  if g not in graphs:
   loc={};dirs={};dest=[];types={};grid={};state={};stack=[]
   def start(name,a):
    parent=stack[-1] if stack else None;stack.append(name)
    if name=='block_type':types[int(a['id'])]=(int(a['width']),int(a['height']))
    elif name=='grid_loc':grid[int(a.get('layer','0')),int(a['x']),int(a['y'])]=int(a['block_type_id'])
    elif name=='node' and parent=='rr_nodes':state['node']=int(a['id']);dirs[state['node']]=a.get('direction')
    elif name=='loc' and parent=='node':loc[state['node']]=tuple(int(a[k]) for k in ['xlow','xhigh','ylow','yhigh'])+(int(a.get('layer','0')),)
    elif name=='edge' and parent=='rr_edges':dest.append(int(a['sink_node']))
   def end(name):assert stack.pop()==name
   parser=xml.parsers.expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
   with Path(g).open('rb') as f:parser.ParseFile(f)
   graphs[g]=loc,dirs,dest,types,grid
  loc,dirs,dest,types,grid=graphs[g];ep=read(c['endpoint']);data=read(c['payload']);points=defaultdict(set)
  for q in ep['connections']:
   for n in [q['source'],q['sink']]:
    xl,xh,yl,yh,z=loc[n];assert xl==xh and yl==yh and types[grid[z,xl,yl]]==(1,1);points[q['net_id']].add((xl,yl,z))
  X=max(x for z,x,y in grid);Y=max(y for z,x,y in grid);boxes={}
  for net,ps in points.items():boxes[net]=[max(0,min(x for x,y,z in ps)-4),min(X,max(x for x,y,z in ps)+3),max(0,min(y for x,y,z in ps)-4),min(Y,max(y for x,y,z in ps)+3),min(z for x,y,z in ps),max(z for x,y,z in ps)]
  assert boxes=={int(n):b for n,b in data['boxes'].items()}
  def outside(n,b):
   xl,xh,yl,yh,z=loc[n];x,y=(xh,yh) if dirs[n]=='DEC_DIR' else (xl,yl);return not (b[0]<=x<=b[1] and b[2]<=y<=b[3] and b[4]<=z<=b[5])
  forecast=read(E/'wbuart_forecasts_v1_2026-10-20/verification.json');out=Path(next(a['output'] for r in forecast['rows'] if r['case']==c['case'] for a in r['arms'] if a['initializer']=='native_retained' and a['timing_policy']=='warm_timing_round_updated'))
  for method,name in [('warm','initial.json'),('primary_round0','round0.json'),('primary_round1','round1.json')]:
   witnesses=[]
   for q in read(out/name)['records']:
    ns={q['source']}|{dest[e] for e in q['answer']['physical_edge_ids']};bad=sorted(n for n in ns if outside(n,boxes[q['net_id']]))
    if bad:witnesses.append({'connection_id':q['connection_id'],'net_id':q['net_id'],'outside_nodes':bad})
   assert witnesses==data['methods'][method]['witnesses']
  bankrow=next(r for r in read(E/'wbuart_sparse_pair_feasibility_v1_2026-10-20/verification.json')['rows'] if r['case']==c['case']);bank=read(bankrow['bank']);badcount=0
  for b,saved in zip(bank,data['bank_candidates']):
   count=0
   for q in b['records']:
    ns={q['source']}|{dest[e] for e in q['answer']['physical_edge_ids']};count+=any(outside(n,boxes[q['net_id']]) for n in ns)
   assert count==saved['outside_connection_count'];badcount+=count>0
  assert badcount==c['bank_candidates_outside_initial_box'];rows.append({'case':c['case'],'NET_boxes':len(boxes),'bank_candidates_outside_initial_box':badcount,'primary_round1_outside_connections':data['methods']['primary_round1']['outside_connection_count']})
 assert len(rows)==9
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL9_INITIAL_BOXES_AND_MODEL_BANK_DRIVE_POINT_WITNESSES_EXPAT_VERIFIED','rows':rows,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Point-terminal/unit-tile assumptions explicitly verified for all routed endpoints; independent graph parser and box reconstruction/model path witnesses. Native final outside counts remain producer parsed; actual runtime box trajectory not observed.'},indent=2)+'\n');print('ALL9_INITIAL_BOXES_AND_MODEL_BANK_DRIVE_POINT_WITNESSES_EXPAT_VERIFIED')
if __name__=='__main__':main()
