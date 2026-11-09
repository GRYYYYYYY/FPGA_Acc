"""Capture native post-sync physical routes and attempt strict unique-pin bundle reloads."""
import json,re,os,shutil,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
from stream_native_route_audit import audit
from audit_native_route import NODE
root=Path(__file__).resolve().parents[1];out=root/'experiments/bitonic_workflow_screened4_resident_staging_n16_canonical_2026-10-07';out.mkdir();work=root/'work/bitonic_workflow_screened4_resident_staging_n16_canonical_2026-10-07';work.mkdir();parent=root/'experiments/bitonic_workflow_screened4_resident_staging_native_import_2026-10-07';v=json.loads((parent/'verification.json').read_text());receipt=json.loads((parent/'receipt.json').read_text());assert sha(parent/'receipt.json')==v['receipt_sha256'];raw=next(x for x in receipt['rows'] if x['count']==16);assert raw['status']=='RAW_NATIVE_FULL_STA_SUCCESS';original={**raw,'files_sha256':raw['files']};r={'results':[{'pair_index':0,'command':raw['command'],'cwd':str(parent/'n16'),'cpd_ns':float(raw['cpd_ns']),'sha256':raw['files']}]};capture=root/'build/native_route_sync_capture_v2_2026-10-06/routecast_sync_capture_vpr';identity=root/'build/native_net_identity_capture_2026-10-06/routecast_net_identity_vpr';env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};graph=original['command'][original['command'].index('--read_rr_graph')+1];xml=ET.parse(graph).getroot();nodes={int(n.get('id')):(n.get('type'),int(n.find('loc').get('xlow')),int(n.find('loc').get('ylow')),int(n.find('loc').get('layer','0')),int(n.find('loc').get('ptc'))) for n in xml.find('rr_nodes')};results=[]
def run(cmd,cwd,log,env):
 with log.open('w') as f:return subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=60).returncode
for row in r['results']:
 assert all(sha(p)==h for p,h in row['sha256'].items());index=row['pair_index'];cwd=work/str(index);cwd.mkdir();cmd=row['command'].copy();cmd[0]=str(capture)
 for n in ('design.net','design.blif','design.place','design.route'):shutil.copyfile(Path(row['cwd'])/n,cwd/n)
 capenv={**env,'ROUTECAST_SYNC_CAPTURE_DIR':str(cwd)};assert run(cmd,cwd,cwd/'capture.log',capenv)==0
 before=audit(graph,cwd/'before_sync.route');after=audit(graph,cwd/'after_sync.route');assert len(after['connections'])==5070 and after['overflow_units']==0
 reload=cwd/'reload';reload.mkdir();shutil.copyfile(cwd/'design.blif',reload/'design.blif');shutil.copyfile(cwd/'design.net.post_routing',reload/'design.net');place=re.sub(r'Netlist_ID:\s*\S+','Netlist_ID: SHA256:'+sha(reload/'design.net'),(cwd/'design.place').read_text(),count=1);(reload/'design.place').write_text(place);icmd=cmd.copy();icmd[0]=str(identity);icmd[icmd.index('--route_file')+1]='missing.route';table=reload/'identity.jsonl';assert run(icmd,reload,reload/'identity.log',{**env,'ROUTECAST_NET_IDENTITY_FILE':str(table)})==1 and table.exists();nets={t['name']:t for t in map(json.loads,table.read_text().splitlines())};sections={};current=None;ambiguous=[];pins=0;changes=0
 for line in (cwd/'after_sync.route').read_text().splitlines():
  m=re.match(r'^Net\s+(\d+)\s+\((.*?)\)',line)
  if m:
   record=nets[m[2]];current=record['net_id'];assert current not in sections;sections[current]=[re.sub(r'^Net\s+\d+',f'Net {current}',line)];changes+=int(current!=int(m[1]));continue
  if current is None:continue
  m=NODE.match(line)
  if m and m[2]=='SINK':
   kind,x,y,layer,klass=nodes[int(m[1])];options=[p for p in record['pins'] if p['index']>0 and (p['x'],p['y'],p['layer'],p['class'])==(x,y,layer,klass)]
   if len(options)!=1:ambiguous.append({'net':record['name'],'sink':int(m[1]),'options':options})
   else:line=re.sub(r'Net_pin_index:\s*\d+',f"Net_pin_index: {options[0]['index']}",line);pins+=1
  sections[current].append(line)
 result={'pair_index':index,'post_sync_route_unchanged':sha(cwd/'before_sync.route')==sha(cwd/'after_sync.route'),'connections':len(after['connections']),'overflow_units':after['overflow_units'],'ambiguous_pins':ambiguous,'net_ids_changed':changes,'remapped_sink_pins':pins,'status':'AMBIGUOUS_PIN_IDENTITY' if ambiguous else 'READY','cwd':str(cwd)}
 if not ambiguous:
  head=(cwd/'design.route').read_text().split('Net ',1)[0];head=re.sub(r'Placement_ID:\s*\S+','Placement_ID: SHA256:'+sha(reload/'design.place'),head);lines=head.splitlines()
  for n in sorted(sections):lines.extend(sections[n])
  (reload/'design.route').write_text('\n'.join(lines)+'\n');cmd[0]=row['command'][0];code=run(cmd,reload,reload/'reload.log',env);log=(reload/'reload.log').read_text();cpd=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log);mis=re.search(r'Found (\d+) mismatches',log);fix=re.search(r'Fixed (\d+) routing traces',log);result.update(exit_code=code,cpd_ns=float(cpd[1]) if cpd else None,sync_mismatches=int(mis[1]) if mis else None,sync_fixups=int(fix[1]) if fix else None,status='RELOADED' if code==0 and 'VPR succeeded' in log else 'RELOAD_FAILED');result['cpd_matches_original']=result['cpd_ns']==row['cpd_ns'];result['reload_command']=cmd
 result['sha256']={str(p):sha(p) for p in cwd.rglob('*') if p.is_file()};results.append(result);print(index,result['status'],len(ambiguous),result.get('cpd_ns'),result.get('sync_mismatches'),flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'source_sha256':sha(Path(__file__)),'parent_receipt_sha256':sha(parent/'receipt.json'),'graph_sha256':sha(graph),'binaries_sha256':{str(p):sha(p) for p in (capture,identity,Path(r['results'][0]['command'][0]))},'scope':'Native before/after sync physical route capture; packed NET identity remapped by name, pin by unique site/class only, digest chain rebound, original VPR FULL reload. Ambiguity is preserved as failure, not guessed. No runtime benefit or production transaction claim.'},indent=2)+'\n')
