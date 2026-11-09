"""Map pre-route packed pins to native identity, serialize new trees, originalFULL/STA."""
import json,os,re,shutil,subprocess
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];parent=root/'experiments/tseng_joint_transfer_2026-10-06';r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json') and v['accepted_paths_checked']==1234;endpoint_dir=root/'experiments/nonzero_rc_tseng_endpoints_2026-10-06';ep=json.loads((endpoint_dir/'endpoints.json').read_text());mapping=json.loads((endpoint_dir/'mapping.json').read_text());assert all(sha(p['path'])==p['sha256'] for p in ep['inputs'].values());src=root/'work/nonzero_rc_tseng_reference128_2026-10-06';out=root/'experiments/tseng_joint_native_import_2026-10-06';out.mkdir();work=root/'work/tseng_joint_native_import_2026-10-06';work.mkdir()
for n in ('design.blif','design.net','design.place'):shutil.copyfile(src/n,work/n)

shared=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';binary=shared/'build_tileplace_vpr/vpr/vpr';identity=root/'build/native_net_identity_capture_2026-10-06/routecast_net_identity_vpr';arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml';graph=Path(ep['inputs']['graph']['path']);cmd=[str(binary),str(arch),'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','design.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--check_route','full'];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};icmd=cmd.copy();icmd[0]=str(identity);icmd[icmd.index('--route_file')+1]='missing.route';table=work/'identity.jsonl'
with (work/'identity.log').open('w') as f:code=subprocess.run(icmd,cwd=work,env={**env,'ROUTECAST_NET_IDENTITY_FILE':str(table)},stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
assert code==1 and table.exists();nets={row['name']:row for row in map(json.loads,table.read_text().splitlines())};details=defaultdict(list)
for d in mapping['pin_details']:
 if d['role']=='SINK':details[d['net_id']].append(d)
offsets=defaultdict(int);bindings={}
for q in ep['connections']:
 net=q['net_id'];d=details[net][offsets[net]];offsets[net]+=1;assert d['rr_node']==q['sink'];name=ep['net_names'][str(net)];record=nets[name];options=[p for p in record['pins'] if p['index']>0 and (p['block'],p['port'],p['bit'],p['physical_pin'])==(d['block'],d['port'],d['bit'],d['physical_pin_ptc'])];assert len(options)==1;bindings[q['connection_id']]={'native_net_id':record['net_id'],'native_pin_index':options[0]['index'],'net_name':name,'packed_pin':d}
xml=ET.parse(graph).getroot();nodes={int(n.get('id')):(n.get('type'),dict(n.find('loc').attrib)) for n in xml.find('rr_nodes')};edges=[(int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))) for e in xml.find('rr_edges')];groups=defaultdict(list)
for q in r['records']:groups[bindings[q['connection_id']]['native_net_id']].append(q)
lines=['Placement_File: design.place Placement_ID: SHA256:'+sha(work/'design.place'),(work/'design.place').read_text().splitlines()[1]+'.','','Routing:',''];sinks=0
for net,qs in sorted(groups.items()):
 lines.extend([f"Net {net} ({bindings[qs[0]['connection_id']]['net_name']})",'']);emitted=set()
 for q in sorted(qs,key=lambda q:bindings[q['connection_id']]['native_pin_index']):
  path=[q['source']];switches=[]
  for eid in q['answer']['physical_edge_ids']:u,node,s=edges[eid];assert u==path[-1];path.append(node);switches.append(s)
  start=0
  if emitted:
   while start+1<len(path) and path[start+1] in emitted:start+=1
   assert path[start] in emitted and all(n not in emitted for n in path[start+1:-1])
  for i in range(start,len(path)):
   n=path[i];kind,loc=nodes[n];lo=f"({loc['xlow']},{loc['ylow']},{loc.get('layer','0')})";hi=f"({loc['xhigh']},{loc['yhigh']},{loc.get('layer','0')})";coords=lo if lo==hi else lo+' to '+hi;label='Track' if kind in ('CHANX','CHANY') else 'Class' if kind in ('SOURCE','SINK') else 'Pin';switch=switches[i] if i<len(switches) else -1;line=f"Node:\t{n}\t {kind} {coords} {label}: {loc['ptc']} Switch: {switch}"
   if i==len(path)-1:assert kind=='SINK';line+=f" Net_pin_index: {bindings[q['connection_id']]['native_pin_index']}";sinks+=1
   lines.append(line);emitted.add(n)
 lines.extend(['',''])
assert sinks==1234;(work/'design.route').write_text('\n'.join(lines)+'\n');(out/'pin_bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
with (work/'import.log').open('w') as f:code=subprocess.run(cmd,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
log=(work/'import.log').read_text();cpd=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log);result={'exit_code':code,'native_success':code==0 and 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log,'cpd_ns':float(cpd[1]) if cpd else None,'connections':sinks,'endpoint_sha256':sha(endpoint_dir/'endpoints.json'),'mapping_sha256':sha(endpoint_dir/'mapping.json'),'command':cmd,'identity_command':icmd,'parent_sha256':sha(parent/'receipt.json'),'pin_bindings_sha256':sha(out/'pin_bindings.json'),'binary_sha256':sha(binary),'identity_binary_sha256':sha(identity),'source_sha256':sha(Path(__file__)),'files_sha256':{str(p):sha(p) for p in work.iterdir() if p.is_file()},'scope':'Pre-route packed-pin identity only maps newly predicted1234 paths; no original route/timing used. Fresh originalFULL/STA analysis; canonical sync/serialization preservation pending independentaudit.'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('ex5p predicted native',code,result['native_success'],result['cpd_ns'])
