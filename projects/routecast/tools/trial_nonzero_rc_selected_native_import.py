"""Serialize independently selected nonzero-RC trees and run original VPR FULL+STA."""
import json,re,shutil,subprocess,os
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];parent=root/'experiments/nonzero_rc_lcv_selection_2026-10-06';selection=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json') and v['complete_selection_verified'];pool=json.loads((root/'experiments/nonzero_rc_pair_avoidance_2026-10-06/receipt.json').read_text());assert selection['parent_sha256']==sha(root/'experiments/nonzero_rc_pair_avoidance_2026-10-06/receipt.json')
baseline=root/'experiments/nonzero_rc_fanout_observable64_2026-10-06';p=json.loads((baseline/'protocol.json').read_text());r=json.loads((baseline/'receipt.json').read_text());assert all(sha(f)==h for f,h in r['files_sha256'].items());src=Path(p['cwd']);graph=src/'rr_graph.xml';xml=ET.parse(graph).getroot();nodes={int(n.get('id')):(n.get('type'),dict(n.find('loc').attrib)) for n in xml.find('rr_nodes')};edges=[(int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))) for e in xml.find('rr_edges')]
out=root/'experiments/nonzero_rc_selected_native_import_2026-10-06';out.mkdir();work=root/'work/nonzero_rc_selected_native_import_2026-10-06';work.mkdir()
for name in ('design.blif','design.net','design.place'):shutil.copyfile(src/name,work/name)
sections={};head=[];net=None
for line in (src/'design.route').read_text().splitlines():
 match=re.match(r'^\s*Net\s+(\d+)\s+\(',line)
 if match:net=int(match[1]);sections[net]=[]
 (head if net is None else sections[net]).append(line)
groups=defaultdict(list)
for g,a in zip(pool['candidates'],selection['selected']):groups[g['key'][0]].append((g['key'][1],g['paths'][a]))
head[0]='Placement_File: design.place Placement_ID: SHA256:'+sha(work/'design.place');serialized=list(head);sinkcount=0
for net,section in sections.items():
 if net not in groups:serialized.extend(section);continue
 serialized.extend([section[0],'']);emitted=set()
 for pin,path_data in sorted(groups[net]):
  path=[];switches=[]
  for eid in path_data['answer']['physical_edge_ids']:
   u,v,s=edges[eid]
   if not path:path.append(u)
   assert path[-1]==u;path.append(v);switches.append(s)
  start=0
  if emitted:
   while start+1<len(path) and path[start+1] in emitted:start+=1
   assert path[start] in emitted and all(n not in emitted for n in path[start+1:-1])
  for i in range(start,len(path)):
   n=path[i];kind,loc=nodes[n];lo=f"({loc['xlow']},{loc['ylow']},{loc.get('layer','0')})";hi=f"({loc['xhigh']},{loc['yhigh']},{loc.get('layer','0')})";coords=lo if lo==hi else lo+' to '+hi;label='Track' if kind in ('CHANX','CHANY') else 'Class' if kind in ('SOURCE','SINK') else 'Pin';switch=switches[i] if i<len(switches) else -1;line=f"Node:\t{n}\t {kind} {coords} {label}: {loc['ptc']} Switch: {switch}"
   if i==len(path)-1:assert kind=='SINK';line+=f' Net_pin_index: {pin}';sinkcount+=1
   serialized.append(line);emitted.add(n)
 serialized.extend(['',''])
assert sinkcount==69;(work/'design.route').write_text('\n'.join(serialized)+'\n');binary=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_vpr/vpr/vpr';cmd=[str(binary),p['command'][1],'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','design.route','--read_rr_graph',str(graph),'--route_chan_width','64','--num_workers','1','--check_route','full'];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
with (work/'import.log').open('w') as stream:code=subprocess.run(cmd,cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=60).returncode
log=(work/'import.log').read_text();cpd=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log);result={'exit_code':code,'native_success':code==0 and 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log,'cpd_ns':float(cpd[1]) if cpd else None,'selected_connections':sinkcount,'selection_sha256':sha(parent/'receipt.json'),'command':cmd,'binary_sha256':sha(binary),'source_sha256':sha(Path(__file__)),'files_sha256':{str(work/n):sha(work/n) for n in ('design.blif','design.net','design.place','design.route','import.log')},'scope':'Original nativeFULL/STA analysis of independently selected complete nonzeroRC tree, no rerouting or original physical reference path copying; packing fixups/full serialization must be reviewed.'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('native import',code,result['native_success'],result['cpd_ns'])
