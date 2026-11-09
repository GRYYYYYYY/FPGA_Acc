"""Native drive-point BB-constrained outsider queries, all CHANNELs including zeros."""
import json,struct,xml.etree.ElementTree as ET
from audit_prince_other_owner_transport_v1 import load,sha,D,R
O=R/'experiments/prince_BB_conditional_demand_v1_2026-10-20'
def main():
 assert not O.exists();O.mkdir();proofp=D/'ownership_verification_v1.json';proof=json.loads(proofp.read_text());bindings={str(proofp):sha(proofp),str(__file__):sha(__file__)};graphs={};rows=[]
 header=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route/route_common.h';bindings[str(header)]=sha(header)
 (O/'protocol.json').write_text(json.dumps(dict(query_rule='All capacity-positive CHANNELs, one cyclic outsider NET whose SAME-phase native BB contains native direction-dependent drive point; skip only if no such outsider. Includes zero occupancy.',predictor='unfitted two-frame mean of coherent other-owner demand; first frame persistence',horizon='next native end-iteration',scope='Development geometric filter diagnostic, not actual expansion trace, reachability, final-target or native utility gate',bindings=dict(bindings)),indent=2)+'\n')
 for case_row in proof['rows']:
  case=case_row['case'];width=case.split('/')[0]
  if width not in graphs:
   gp=R/'experiments/prince_native_cohort_v1_2026-10-20'/width/'source/rr_graph.xml';vp=R/'experiments/prince_quality_domains_v1_2026-10-20'/width/'verification.json';assert sha(gp)==json.loads(vp.read_text())['graph_sha256'];bindings[str(gp)]=sha(gp);bindings[str(vp)]=sha(vp);points={}
   for node in ET.parse(gp).getroot().findall('rr_nodes/node'):
    if node.get('type') not in ['CHANX','CHANY'] or int(node.get('capacity'))<=0:continue
    loc=node.find('loc');end='high' if node.get('direction')=='DEC_DIR' else 'low';assert node.get('direction') in ['DEC_DIR','INC_DIR','BI_DIR'];points[int(node.get('id'))]=(int(loc.get('x'+end)),int(loc.get('y'+end)),int(loc.get('layer','0')))
   graphs[width]=points
  points=graphs[width];paths=sorted((D/case/'capture/owners').glob('*.bin'),key=lambda p:int(p.stem.split('_')[-1]));previous=None;current=load(paths[0])
  for p in paths:assert sha(p)==proof['bindings'][str(p)];bindings[str(p)]=sha(p)
  for path in paths[1:]:
   i,owners,counts=current;nets=sorted(owners);bp=D/case/'capture/boundary'/f'boxes_{i}.bin';raw=bp.read_bytes();assert raw[:8]==b'RCBOX001' and struct.unpack_from('<Q',raw,8)[0]==i;boxes={n:b for n,*b in struct.iter_unpack('<Q6i',raw[24:])};bindings[str(bp)]=sha(bp);eligible={}
   for point in set(points.values()):
    x,y,z=point;eligible[point]=set(n for n in nets if boxes[n][0]<=x<=boxes[n][1] and boxes[n][2]<=y<=boxes[n][3] and boxes[n][4]<=z<=boxes[n][5])
   oldowners,oldcounts=(previous[1],previous[2]) if previous else (owners,counts);predictions=[];skipped=zero=0
   for node,point in sorted(points.items()):
    allowed=eligible[point];start=node%len(nets);chosen=None
    for offset in range(len(nets)):
     net=nets[(start+offset)%len(nets)]
     if net in allowed and node not in owners[net]:chosen=net;break
    if chosen is None:skipped+=1;continue
    zero+=counts[node]==0;predictions.append((chosen,node,2*counts[node],counts[node]+oldcounts[node]-int(node in oldowners[chosen])))
   j,future,fc=load(path);err=[0,0];exact=[0,0];entered=0
   for net,node,baseline,candidate in predictions:
    truth=2*(fc[node]-int(node in future[net]));assert min(candidate,truth)>=0;entered+=node in future[net]
    for k,value in enumerate([baseline,candidate]):err[k]+=abs(value-truth);exact[k]+=value==truth
   rows.append(dict(case=case,iteration=i,queries=len(predictions),zero_occupancy_queries=zero,skipped_no_BB_outsider=skipped,queried_NET_enters_next_frame=entered,persistence_abs_error_half_units=err[0],two_frame_abs_error_half_units=err[1],persistence_exact=exact[0],two_frame_exact=exact[1]));previous,current=current,(j,future,fc)
 assert len(rows)==218;keys=[k for k in rows[0] if k not in ['case','iteration']];totals={k:sum(x[k] for x in rows) for k in keys};cases={case:{k:sum(x[k] for x in rows if x['case']==case) for k in keys} for case in sorted({x['case'] for x in rows})};assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(rows=rows,totals=totals,cases=cases,bindings=bindings,status='BB_GEOMETRIC_QUERY_SCREEN_COMPLETE_NOT_NATIVE_UTILITY'),indent=2)+'\n');print(json.dumps(dict(totals=totals,cases=cases)))
if __name__=='__main__':main()
