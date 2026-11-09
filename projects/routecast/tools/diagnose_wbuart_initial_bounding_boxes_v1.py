"""Source-faithful initial NET boxes and drive-point membership diagnostics."""
import json,hashlib,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from native_route_ledger_import_compact import physical_paths
E=R/'experiments';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route';D=E/'wbuart_initial_bbox_diagnosis_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);W=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';F=E/'wbuart_forecasts_v1_2026-10-20/verification.json';P=E/'wbuart_sparse_pair_feasibility_v1_2026-10-20/verification.json';files=[Path(__file__),W,F,P,V/'route_common.h',V/'route_common.cpp',V/'connection_router.cpp',V/'route.cpp'];bindings={str(p):sha(p) for p in files};graphs={};rows=[]
 for c in read(W)['comparisons']:
  s=read(c['specification']);ep=read(s['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:
   nodes=[];dest=[];grid={};types={}
   for _,e in ET.iterparse(g):
    if e.tag=='block_type':types[int(e.get('id'))]=(int(e.get('width')),int(e.get('height')))
    elif e.tag=='grid_loc':grid[int(e.get('layer','0')),int(e.get('x')),int(e.get('y'))]=(int(e.get('block_type_id')),int(e.get('width_offset')),int(e.get('height_offset')))
    elif e.tag=='node' and e.get('capacity') is not None:
     assert int(e.get('id'))==len(nodes);a=e.find('loc').attrib;nodes.append({'kind':e.get('type'),'direction':e.get('direction'),'xlow':int(a['xlow']),'xhigh':int(a['xhigh']),'ylow':int(a['ylow']),'yhigh':int(a['yhigh']),'layer':int(a.get('layer','0'))})
    elif e.tag=='edge':dest.append(int(e.get('sink_node')))
   graphs[g]=(nodes,dest,grid,types);bindings[g]=sha(g)
  nodes,dest,grid,types=graphs[g];width=max(x for layer,x,y in grid)+1;height=max(y for layer,x,y in grid)+1;netqueries=defaultdict(list)
  for q in ep['connections']:netqueries[q['net_id']].append(q)
  factor=3;boxes={}
  for net,qs in netqueries.items():
   driver=nodes[qs[0]['source']];xmin,xmax,ymin,ymax,lo,hi=driver['xlow'],driver['xhigh'],driver['ylow'],driver['yhigh'],driver['layer'],driver['layer']
   for q in qs:
    sink=nodes[q['sink']];assert sink['kind']=='SINK';kind,dx,dy=grid[sink['layer'],sink['xlow'],sink['ylow']];tw,th=types[kind];x,y=sink['xlow']-dx,sink['ylow']-dy;xmin=min(xmin,x);xmax=max(xmax,x+tw-1);ymin=min(ymin,y);ymax=max(ymax,y+th-1);lo=min(lo,sink['layer']);hi=max(hi,sink['layer'])
   boxes[net]=[max(0,xmin-1-factor),min(width-1,xmax+factor),max(0,ymin-1-factor),min(height-1,ymax+factor),lo,hi]
  def inside(node,box):
   n=nodes[node];dec=n['direction']=='DEC_DIR';x=n['xhigh'] if dec else n['xlow'];y=n['yhigh'] if dec else n['ylow'];a,b,c,d,lo,hi=box;return a<=x<=b and c<=y<=d and lo<=n['layer']<=hi
  def summarize(records):
   bad=[];outside_nodes=set();badnets=set()
   for q in records:
    used={q['source']}|{dest[e] for e in q['answer']['physical_edge_ids']};outside=sorted(n for n in used if not inside(n,boxes[q['net_id']]))
    if outside:bad.append({'connection_id':q['connection_id'],'net_id':q['net_id'],'outside_nodes':outside});outside_nodes.update(outside);badnets.add(q['net_id'])
   return {'connections':len(records),'outside_connection_count':len(bad),'outside_NET_count':len(badnets),'outside_unique_node_count':len(outside_nodes),'witnesses':bad}
  arm=next(a for r in read(F)['rows'] if r['case']==c['case'] for a in r['arms'] if a['initializer']=='native_retained' and a['timing_policy']=='warm_timing_round_updated');methods={'warm':str(Path(arm['output'])/'initial.json'),'primary_round0':str(Path(arm['output'])/'round0.json'),'primary_round1':str(Path(arm['output'])/'round1.json')};result={name:summarize(read(p)['records']) for name,p in methods.items()};bankrow=next(x for x in read(P)['rows'] if x['case']==c['case']);bank=read(bankrow['bank']);candidate_results=[{'candidate_id':b['id'],'net_id':b['net_id'],**summarize(b['records'])} for b in bank];nameid={name:int(n) for n,name in ep['net_names'].items()};native={}
  for ref,path in [('cold',Path(s['label_physical_audit']).parent/'output.route'),('source_restart',E/'wbuart_target_source_restart_reference_v1_2026-10-20'/c['case']/'output.route')]:
   outside=Counter();total=0
   for name,paths in physical_paths(path).items():
    if name not in nameid:continue
    net=nameid[name]
    if net not in boxes:continue
    for branch in paths:total+=1;outside[net]+=any(not inside(n,boxes[net]) for n,sw in branch)
   assert total==2493;native[ref]={'connections':total,'outside_connection_count':sum(outside.values()),'outside_NET_count':sum(x>0 for x in outside.values())};bindings[str(path)]=sha(path)
  folder=D/c['case'];folder.mkdir(parents=True);payload=folder/'details.json';payload.write_text(json.dumps({'boxes':boxes,'methods':result,'bank_candidates':candidate_results,'native_final':native})+'\n');summary={'case':c['case'],'payload':str(payload),'endpoint':s['endpoint'],'graph':g,'initial_full_grid_NET_boxes':sum(b==[0,width-1,0,height-1,0,0] for b in boxes.values()),'NETs':len(boxes),'methods':{n:{k:x for k,x in a.items() if k!='witnesses'} for n,a in result.items()},'bank_candidates':len(bank),'bank_candidates_outside_initial_box':sum(a['outside_connection_count']>0 for a in candidate_results),'native_final':native};rows.append(summary);print(c['case'],summary['bank_candidates_outside_initial_box'],summary['methods']['primary_round1']['outside_connection_count'],native,flush=True)
  for p in [payload,Path(s['endpoint']),Path(bankrow['bank']),*map(Path,methods.values())]:bindings[str(p)]=sha(p)
 assert len(rows)==9
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_INITIAL_NATIVE_NET_BOX_AND_DRIVE_POINT_PATH_SCREENING_COMPLETE','rows':rows,'bindings':bindings,'scope':'Reconstruction of initial NET bbox factor3 including sink tile footprints, low-side minus1 and DEC drive-point predicate. Does not observe actual per-call/dynamic/retry boxes or RCV bypass; outside initial box is not proof invalid native path or quality cause. No search clipping or routing.'},indent=2)+'\n')
if __name__=='__main__':main()
