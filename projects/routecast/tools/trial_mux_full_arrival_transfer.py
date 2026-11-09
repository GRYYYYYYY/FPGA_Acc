"""Full-fanin arrival update from candidate RR, carrying old local edge delays."""
import json,xml.etree.ElementTree as ET
from fractions import Fraction
from collections import defaultdict,deque
from pathlib import Path
from pre_route_endpoints import sha,placements
ROOT=Path(__file__).resolve().parents[1];mappedroot=ROOT/'experiments/mux_full_timing_rr_2026-10-06';graphroot=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06';parent=ROOT/'experiments/mux_retained_joint_reroute_2026-10-06';native=ROOT/'experiments/mux_retained_joint_quality_gate_2026-10-06';out=ROOT/'experiments/mux_full_arrival_transfer_2026-10-06';out.mkdir();cases=json.loads((parent/'protocol.json').read_text())['cases'];quality=json.loads((native/'verification.json').read_text());rows=[];bindings={}
for case,qr in zip(cases,quality['rows']):
 w,i=case['width'],case['index']
 if qr['status']!='RELOADED':rows.append(dict(width=w,index=i,status=qr['status']));continue
 tgfile=graphroot/f'w{w}_timing_graph.json';tg=json.loads(tgfile.read_text());mp=mappedroot/f'w{w}.json';mapping=json.loads(mp.read_text());prediction=parent/f'w{w}_m{i}/prediction.json';candidate=json.loads(prediction.read_text());ep=json.loads(Path(case['target']).read_text());pos=placements(ep['inputs']['place']['path'],ep['inputs']['net']['sha256']);xml=ET.parse(ep['inputs']['graph']['path']).getroot();loc={int(n.get('id')):n.find('loc').attrib for n in xml.find('rr_nodes')};delays={}
 for rec in candidate['records']:
  site=loc[rec['sink']];key=(ep['net_names'][str(rec['net_id'])],*(int(site.get(k,'0'))for k in('xlow','ylow','layer','ptc')));assert key not in delays;delays[key]=Fraction(rec['answer']['delay'],candidate['scale'])
 changed={}
 for eid,m in mapping['external_edges'].items():
  x,y,_,layer,_=pos[m['sink_cluster']];sink_class=int(loc[m['branch']['sink']]['ptc']);key=(m['atom_net'],x,y,layer,sink_class);changed[eid]=delays[key]+Fraction(m['old_local_offset_seconds'])
 adj=defaultdict(list);indeg={int(n):0 for n in tg['nodes']}
 for eid,e in tg['edges'].items():
  if not e['disabled']:adj[e['source']].append((e['sink'],eid));indeg[e['sink']]+=1
 queue=deque(sorted(n for n in indeg if not indeg[n]));arr={n:Fraction(0)for n in queue};back={};order=[]
 while queue:
  u=queue.popleft();order.append(u)
  for v,eid in adj[u]:
   delay=changed.get(eid,Fraction(tg['edges'][eid]['max_delay_seconds']));nd=arr[u]+delay
   if v not in arr or nd>arr[v]:arr[v]=nd;back[v]=(u,eid)
   indeg[v]-=1
   if indeg[v]==0:queue.append(v)
 assert len(order)==len(tg['nodes']);sinks=[int(n)for n,k in tg['nodes'].items()if k=='SINK'];worst=max(sinks,key=lambda n:arr[n]);cpd=arr[worst]*10**9;node=worst;path=[]
 while node in back:node,eid=back[node];path.append(eid)
 file=out/f'w{w}_m{i}.json';file.write_text(json.dumps(dict(predicted_cpd_ns=str(cpd),worst_sink_node=worst,worst_path_edge_ids=list(reversed(path)),updated_external_edge_seconds={e:str(v)for e,v in changed.items()},arrival_seconds={str(n):str(v)for n,v in arr.items()}),indent=2)+'\n');rows.append(dict(width=w,index=i,status='FULL_FANIN_TRANSFER',predicted_cpd_ns=float(cpd),native_candidate_cpd_ns=qr['predicted_cpd_ns'],difference_ns=float(cpd)-qr['predicted_cpd_ns'],sha256=sha(file)));print(rows[-1],flush=True)
 for p in(tgfile,mp,prediction,Path(case['target']),Path(ep['inputs']['place']['path'])):bindings[str(p)]=sha(p)
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),quality_verification_sha256=sha(native/'verification.json'),bindings=bindings,rows=rows,scope='All12 outcomes retained; fourcompleteactualRRforecasts transferred through completeoldtiminggraph with oldlocal/primitive/internal delays fixed. Retrospective modelvalidation, not nativeSTA substitute or prospective gains.'),indent=2)+'\n')
