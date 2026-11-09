"""Authenticated native-name/class identity remap for coherent bundle reload."""
import json,re,shutil,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from audit_native_route import NET,NODE
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'native_identity_remapped_reload_2026-10-06';work=root/'work/native_identity_remapped_reload_2026-10-06';out.mkdir();work.mkdir();identity=base/'native_net_identity_capture_2026-10-06';receipt=json.loads((identity/'receipt.json').read_text());tables={}
for case in receipt['cases']:
 file=identity/f"{case['case']}.jsonl";assert sha(file)==case['identity_sha256'];tables[case['case']]=[json.loads(x) for x in file.read_text().splitlines()]
old={r['net_id']:r for r in tables['original']};new={r['name']:r for r in tables['synchronized']};assert {r['name'] for r in old.values()}==set(new);source=root/'work/native_synchronized_bundle_reload_2026-10-06/rebound_bundle';command=json.loads((base/'native_synchronized_bundle_reload_2026-10-06/rebound_bundle_command.json').read_text())['command'];graph=command[command.index('--read_rr_graph')+1];xml=ET.parse(graph).getroot();nodes={}
for n in xml.find('rr_nodes'):
 loc=n.find('loc');nodes[int(n.get('id'))]=(n.get('type'),int(loc.get('xlow')),int(loc.get('ylow')),int(loc.get('layer','0')),int(loc.get('ptc')))
sections={};head=[];current=None;changes=[]
for line in (source/'design.route').read_text().splitlines():
 match=NET.match(line)
 if match:
  oldid=int(match[1]);assert oldid in old;record=new[old[oldid]['name']];current=record['net_id'];assert current not in sections;line=re.sub(r'^Net\s+\d+',f'Net {current}',line);sections[current]=[line];continue
 if current is None:head.append(line);continue
 match=NODE.match(line)
 if match and match[2]=='SINK':
  kind,x,y,layer,klass=nodes[int(match[1])];options=[p for p in record['pins'] if p['index']>0 and (p['x'],p['y'],p['layer'],p['class'])==(x,y,layer,klass)];assert len(options)==1;pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]);newpin=options[0]['index'];line=re.sub(r'Net_pin_index:\s*\d+',f'Net_pin_index: {newpin}',line);changes.append({'old_net_id':oldid,'new_net_id':current,'name':record['name'],'sink':int(match[1]),'old_pin_index':pin,'new_pin_index':newpin,'block':options[0]['block']})
 sections[current].append(line)
for n in ('design.blif','design.net','design.place'):shutil.copyfile(source/n,work/n)
lines=head.copy()
for net in sorted(sections):lines.extend(sections[net])
(work/'design.route').write_text('\n'.join(lines)+'\n');shutil.copyfile(work/'design.route',out/'remapped.route');(out/'mapping.json').write_text(json.dumps(changes,indent=2)+'\n');assert len(changes)==129
with (out/'reload.log').open('w') as log:code=subprocess.run(command,cwd=work,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
text=(out/'reload.log').read_text();match=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',text);m=re.search(r'Found (\d+) mismatches between routing and packing results',text);f=re.search(r'Fixed (\d+) routing traces',text);(out/'receipt.json').write_text(json.dumps({'identity_receipt_sha256':sha(identity/'receipt.json'),'mapping_sha256':sha(out/'mapping.json'),'route_sha256':sha(out/'remapped.route'),'log_sha256':sha(out/'reload.log'),'exit_code':code,'success':code==0 and 'VPR succeeded' in text,'cpd_ns':float(match[1]) if match else None,'sync_mismatches':int(m[1]) if m else None,'sync_fixups':int(f[1]) if f else None,'scope':'Coherent synchronized packed/placement/predictor route reload after captured native NET-name and unique terminal class/coordinate pin-index remap. Ambiguous mapping rejected; no formal atom equivalence or seed-preserving reroute/performance.'},indent=2)+'\n');print(code,match[1] if match else None,m[1] if m else None,f[1] if f else None)
