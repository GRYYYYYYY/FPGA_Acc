"""Accepted real-move bundle remapping from fresh native identity captures."""
import json,re,os,shutil,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from audit_native_route import NET,NODE
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/accepted_native_bundle_reload_2026-10-06';work=root/'work/accepted_native_bundle_reload_2026-10-06';out.mkdir();work.mkdir();parent=root/'experiments/native_candidate_move_accept_v3_2026-10-06';record=next(v for v in json.loads((parent/'receipt.json').read_text())['results'] if v['case']=='accept');src=root/'work/native_candidate_move_accept_v3_2026-10-06/accept';assert sha(src/'output.route')==record['route_sha256'] and sha(src/'design.net.post_routing')==record['packed_sha256'];cmd=record['command'].copy();cmd[0]=str(root/'build/native_net_identity_capture_2026-10-06/routecast_net_identity_vpr');cmd[cmd.index('--route')]='--analysis';cmd[cmd.index('--route_file')+1]='missing.route';graph=cmd[cmd.index('--read_rr_graph')+1];tables={};captures=[]
for name in ('original','synchronized'):
 cwd=work/name;cwd.mkdir();shutil.copyfile(src/'design.blif',cwd/'design.blif');shutil.copyfile(src/('design.net' if name=='original' else 'design.net.post_routing'),cwd/'design.net');place=(src/'accepted.place').read_text();place=re.sub(r'Netlist_ID:\s*\S+',f'Netlist_ID: SHA256:{sha(cwd/"design.net")}',place,count=1);(cwd/'design.place').write_text(place);env=os.environ.copy();env['ROUTECAST_NET_IDENTITY_FILE']=str(out/(name+'.jsonl'))
 with (out/(name+'.log')).open('w') as f:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
 assert code==1 and (out/(name+'.jsonl')).exists();tables[name]=[json.loads(line) for line in (out/(name+'.jsonl')).read_text().splitlines()];captures.append({'case':name,'exit_code':code,'identity_sha256':sha(out/(name+'.jsonl')),'packed_sha256':sha(cwd/'design.net'),'placement_sha256':sha(cwd/'design.place')})
old={r['net_id']:r for r in tables['original']};new={r['name']:r for r in tables['synchronized']};assert {r['name'] for r in old.values()}==set(new)
xml=ET.parse(graph).getroot();nodes={}
for n in xml.find('rr_nodes'):
 loc=n.find('loc');nodes[int(n.get('id'))]=(n.get('type'),int(loc.get('xlow')),int(loc.get('ylow')),int(loc.get('layer','0')),int(loc.get('ptc')))
sections={};head=[];current=None;changes=[]
for line in (src/'output.route').read_text().splitlines():
 match=re.match(r'^Net\s+(\d+)\s+\((.*?)\)',line)
 if match:
  oid=int(match[1]);record_new=new[old[oid]['name']];assert record_new['name']==match[2];current=record_new['net_id'];assert current not in sections;sections[current]=[re.sub(r'^Net\s+\d+',f'Net {current}',line)];continue
 if current is None:head.append(line);continue
 match=NODE.match(line)
 if match and match[2]=='SINK':
  kind,x,y,layer,klass=nodes[int(match[1])];options=[p for p in record_new['pins'] if p['index']>0 and (p['x'],p['y'],p['layer'],p['class'])==(x,y,layer,klass)];assert len(options)==1,(record_new['name'],options);oldpin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]);newpin=options[0]['index'];line=re.sub(r'Net_pin_index:\s*\d+',f'Net_pin_index: {newpin}',line);changes.append({'old_net':oid,'new_net':current,'name':record_new['name'],'sink':int(match[1]),'old_pin':oldpin,'new_pin':newpin})
 sections[current].append(line)
assert len(changes)==129
cwd=work/'synchronized';head=[re.sub(r'Placement_ID:\s*\S+',f'Placement_ID: SHA256:{sha(cwd/"design.place")}',line) for line in head];lines=head.copy()
for n in sorted(sections):lines.extend(sections[n])
(cwd/'design.route').write_text('\n'.join(lines)+'\n');(out/'mapping.json').write_text(json.dumps(changes,indent=2)+'\n');shutil.copyfile(cwd/'design.route',out/'remapped.route');cmd[cmd.index('--route_file')+1]='design.route';env=os.environ.copy();env.pop('ROUTECAST_NET_IDENTITY_FILE',None)
with (out/'reload.log').open('w') as f:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
text=(out/'reload.log').read_text();result={'exit_code':code,'captures':captures,'net_ids_changed':sum(old[n]['net_id']!=new[old[n]['name']]['net_id'] for n in old),'route_sha256':sha(cwd/'design.route'),'command':cmd,'cwd':str(cwd),'scope':'Crossprocess accepted moved state reload after postpacked identity remap; no performance or general ambiguous-pin claim.'}
if code==0:
 a=audit(graph,cwd/'design.route');assert len(a['connections'])==129 and a['overflow_units']==0;(out/'physical_audit.json').write_text(json.dumps(a,indent=2)+'\n');result.update(cpd_ns=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[1]),sync_mismatches=int(re.search(r'Found (\d+) mismatches',text)[1]),sync_fixups=int(re.search(r'Fixed (\d+) routing traces',text)[1]))
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
