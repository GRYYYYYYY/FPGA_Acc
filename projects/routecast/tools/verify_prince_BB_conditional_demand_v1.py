"""Expat drive points and inverse owner sets; independent cyclic BB selection."""
import json,struct,bisect,xml.parsers.expat
from audit_prince_other_owner_transport_v1 import load,sha,D,R
O=R/'experiments/prince_BB_conditional_demand_v1_2026-10-20'
def graph(path):
 points={};active=None
 def start(tag,a):
  nonlocal active
  if tag=='node':active=a if a.get('type') in ['CHANX','CHANY'] and int(a['capacity'])>0 else None
  if tag=='loc' and active:
   high=active['direction']=='DEC_DIR';points[int(active['id'])]=(int(a['xhigh' if high else 'xlow']),int(a['yhigh' if high else 'ylow']),int(a.get('layer',0)))
 def end(tag):
  nonlocal active
  if tag=='node':active=None
 p=xml.parsers.expat.ParserCreate();p.StartElementHandler=start;p.EndElementHandler=end
 with path.open('rb') as f:p.ParseFile(f)
 return points
def frame(path):
 i,owners,_=load(path);inverse={}
 for net,nodes in owners.items():
  for node in nodes:inverse.setdefault(node,set()).add(net)
 return i,sorted(owners),inverse
def main():
 source=O/'verification.json';v=json.loads(source.read_text());expected={(x['case'],x['iteration']):x for x in v['rows']};graphs={};checked=0
 for case in v['cases']:
  width=case.split('/')[0]
  if width not in graphs:graphs[width]=graph(R/'experiments/prince_native_cohort_v1_2026-10-20'/width/'source/rr_graph.xml')
  points=graphs[width];paths=sorted((D/case/'capture/owners').glob('*.bin'),key=lambda p:int(p.stem.split('_')[-1]));previous=None;current=frame(paths[0])
  for path in paths[1:]:
   future=frame(path);i,nets,a=current;old=previous[2] if previous else a;new=future[2];raw=(D/case/'capture/boundary'/f'boxes_{i}.bin').read_bytes();boxes={n:b for n,*b in struct.iter_unpack('<Q6i',raw[24:])};eligible={}
   for point in set(points.values()):
    eligible[point]=[idx for idx,net in enumerate(nets) if all(lo<=coord<=hi for coord,lo,hi in zip(point,boxes[net][::2],boxes[net][1::2]))]
   queries=zero=entered=skipped=0;errors=[0,0];exact=[0,0]
   for node,point in points.items():
    candidates=eligible[point];start=bisect.bisect_left(candidates,node%len(nets));chosen=None
    for offset in range(len(candidates)):
     net=nets[candidates[(start+offset)%len(candidates)]]
     if net not in a.get(node,set()):chosen=net;break
    if chosen is None:skipped+=1;continue
    now=len(a.get(node,set())-{chosen});before=len(old.get(node,set())-{chosen});truth=2*len(new.get(node,set())-{chosen});queries+=1;zero+=not a.get(node);entered+=chosen in new.get(node,set())
    for k,value in enumerate([2*now,now+before]):errors[k]+=abs(value-truth);exact[k]+=value==truth
   row=expected[case,i];assert [queries,zero,skipped,entered,*errors,*exact]==[row[k] for k in ['queries','zero_occupancy_queries','skipped_no_BB_outsider','queried_NET_enters_next_frame','persistence_abs_error_half_units','two_frame_abs_error_half_units','persistence_exact','two_frame_exact']];checked+=queries;previous,current=current,future
 assert checked==v['totals']['queries'];out=O/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL_BB_QUERY_METRICS_RECONCILED',queries=checked,pairs=len(expected),method='Expat graph coordinates; axis-pair containment; bisect cyclic eligible indices; inverse owner sets',bindings={str(source):sha(source),str(__file__):sha(__file__)}),indent=2)+'\n');print('BB_QUERY_INDEPENDENT_PASS',checked)
if __name__=='__main__':main()
