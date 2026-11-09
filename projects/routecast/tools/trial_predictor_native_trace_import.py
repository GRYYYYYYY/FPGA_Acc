"""Replay serializer with native sink pin identity, then actual VPR import."""
import json,re,shutil,subprocess,time
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET
from audit_native_route import NET,NODE
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'predictor_native_trace_import_2026-10-06';work=root/'work/predictor_native_trace_import_2026-10-06';out.mkdir();work.mkdir();shutil.copyfile(Path(__file__),out/'source.py');parent=base/'multiplier_live_native_budget_pair_transaction_2026-10-06';receipt=json.loads((parent/'receipt.json').read_text());predfile=parent/'prediction.json';assert sha(predfile)==receipt['prediction_sha256'];pred=json.loads(predfile.read_text());proof=json.loads((base/'multiplier_live_native_budget_pair_xml_audit_2026-10-06/verification.json').read_text());assert proof['inputs_sha256'][str(predfile.parent/'mult_6x6_net_4_11_26_candidate.json')]==sha(predfile);assert all(sha(p)==h for p,h in proof['inputs_sha256'].items());control=json.loads((base/'native_zero_pressure_control_2026-10-06/receipt.json').read_text());inputs=control['inputs'];native=root/'work/native_zero_pressure_control_2026-10-06/0_off/design.route';assert sha(native)==control['results'][0]['route_sha256'];graph=inputs['rr_graph'];xml=ET.parse(graph['path']).getroot();assert sha(graph['path'])==graph['sha256'];nodes={};edges=[]
for n in xml.find('rr_nodes'):
 loc=n.find('loc');nodes[int(n.get('id'))]=(n.get('type'),{k:int(loc.get(k,'0')) for k in ('xlow','ylow','xhigh','yhigh','ptc','layer')})
for e in xml.find('rr_edges'):edges.append((int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))))
text=native.read_text();sections={};head=[];net=None;source=None;pins=defaultdict(list)
for line in text.splitlines():
 m=NET.match(line)
 if m:net=int(m[1]);sections[net]=[line];source=None;continue
 if net is None:head.append(line);continue
 sections[net].append(line);m=NODE.match(line)
 if m:
  nid=int(m[1]);kind=m[2]
  if kind=='SOURCE':source=nid
  if kind=='SINK':
   pin=re.search(r'Net_pin_index:\s*(\d+)',line);assert pin;pins[(net,source,nid)].append(int(pin[1]))
groups=defaultdict(list)
for r in pred['connections']:groups[r['net_id']].append(r)
assert all(len(pins[(r['net_id'],r['source'],r['sink'])])==1 for r in pred['connections']);lines=head.copy();sinkcount=0
for net,section in sections.items():
 if net not in groups:lines.extend(section);continue
 lines.extend([section[0],'']);emitted=set()
 for row in sorted(groups[net],key=lambda r:r['connection_id']):
  pathnodes=[row['source']];switches=[]
  for eid in row['physical_edge_ids']:
   u,v,s=edges[eid];assert u==pathnodes[-1];pathnodes.append(v);switches.append(s)
  assert pathnodes[-1]==row['sink'];assert len(pathnodes)==len(set(pathnodes));start=0
  if emitted:
   while start+1<len(pathnodes) and pathnodes[start+1] in emitted:start+=1
   assert pathnodes[start] in emitted and all(n not in emitted for n in pathnodes[start+1:-1])
  for index in range(start,len(pathnodes)):
   nid=pathnodes[index];kind,loc=nodes[nid];a=f"({loc['xlow']},{loc['ylow']},{loc['layer']})";b=f"({loc['xhigh']},{loc['yhigh']},{loc['layer']})";coords=a if a==b else a+' to '+b;label='Track' if kind in ('CHANX','CHANY') else 'Class' if kind in ('SOURCE','SINK') else 'Pin';switch=switches[index] if index<len(switches) else -1;line=f"Node:\t{nid}\t {kind} {coords}  {label}: {loc['ptc']}  Switch: {switch}"
   if kind=='SINK':line+=f" Net_pin_index: {pins[(net,row['source'],row['sink'])][0]}";sinkcount+=1
   lines.append(line);emitted.add(nid)
 lines.extend(['',''])
assert sinkcount==129
for key,name in (('atom','design.blif'),('packed_netlist','design.net')):shutil.copyfile(inputs[key]['path'],work/name)
place=base/'multiplier_placement_swap_2026-10-06/mult_6x6/swapped.place';shutil.copyfile(place,work/'design.place');(work/'design.route').write_text('\n'.join(lines)+'\n');shutil.copyfile(work/'design.route',out/'predictor.route');binary=root/'build/native_pressure_feedback_v2_2026-10-06/routecast_pressure_vpr';cmd=[str(binary),inputs['architecture']['path'],'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','design.route','--read_rr_graph',graph['path'],'--route_chan_width','300','--num_workers','1'];(out/'command.json').write_text(json.dumps({'command':cmd,'cwd':str(work)})+'\n');start=time.perf_counter()
with (out/'import.log').open('w') as log:code=subprocess.run(cmd,cwd=work,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
log=(out/'import.log').read_text();success=code==0 and 'VPR succeeded' in log;match=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',log);(out/'receipt.json').write_text(json.dumps({'source_sha256':sha(out/'source.py'),'predictor_prediction_sha256':sha(predfile),'native_pin_identity_reference_sha256':sha(native),'serialized_route_sha256':sha(out/'predictor.route'),'graph_sha256':sha(graph['path']),'placement_sha256':sha(place),'log_sha256':sha(out/'import.log'),'exit_code':code,'native_import_success':success,'cpd_ns':float(match[1]) if match else None,'wall_s':time.perf_counter()-start,'scope':'Actual predictor path serialization and native analysis-only route-tree import. NET/SOURCE/rawSINK singleton Net_pin_index comes from existing native route, explicit postroute replay; no new pre-route packed pin mapping, persistent rerouting or performance claim.'},indent=2)+'\n');print(code,success,match[1] if match else None)
