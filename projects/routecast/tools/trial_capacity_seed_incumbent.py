"""Matched guard on/off, including deliberately timing-insensitive repair."""
import json,re,os,shutil,subprocess
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/capacity_seed_incumbent_2026-10-06';out.mkdir();work=root/'work/capacity_seed_incumbent_2026-10-06';work.mkdir();parent=root/'experiments/capacity_synchronized_reload_2026-10-06';pr=json.loads((parent/'receipt.json').read_text());proof=json.loads((parent/'verification.json').read_text());assert sha(parent/'receipt.json')==proof['receipt_sha256'];build=root/'build/capacity_seed_incumbent_2026-10-06';br=json.loads((build/'receipt.json').read_text());binary=build/'guard_vpr';assert sha(binary)==br['binary_sha256'];results=[];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
for pair,crit in [(8,'0.99'),(8,'0'),(1,'0'),(19,'0.99')]:
 row=pr['results'][pair];source=Path(row['cwd'])/'reload';assert all(sha(p)==h for p,h in row['sha256'].items());route=(source/'design.route').read_text();sections=re.split(r'(?=^Net\s+\d+\s+\()',route,flags=re.M);names=[]
 for section in sections:
  m=re.match(r'^Net\s+\d+\s+\((.*?)\)',section)
  if m and re.search(r'^Node:\s*\d+\s+SOURCE\b',section,re.M):names.append(m[1])
 for guard in (False,True):
  case=f'pair_{pair}_crit_{crit}_guard_{int(guard)}';cwd=work/case;cwd.mkdir()
  for n in ('design.net','design.place','design.blif'):shutil.copyfile(source/n,cwd/n)
  shutil.copyfile(source/'design.route',cwd/'seed.route');listfile=cwd/'repair_names.txt';listfile.write_text('\n'.join(sorted(names))+'\n');cmd=row['reload_command'].copy();cmd[0]=str(binary);cmd[cmd.index('--analysis')]='--route';cmd[cmd.index('--route_file')+1]='output.route';cmd+=['--max_criticality',crit];runenv={**env,'ROUTECAST_NATIVE_SEED':str(cwd/'seed.route'),'ROUTECAST_REPAIR_NET_NAMES':str(listfile)}
  if guard:runenv['ROUTECAST_SEED_INCUMBENT']='1'
  with (cwd/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=cwd,env=runenv,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
  log=(cwd/'run.log').read_text();assert code==0 and 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log;cpd=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1]);graph=cmd[cmd.index('--read_rr_graph')+1];physical=audit(graph,cwd/'output.route');assert len(physical['connections'])==516 and not physical['overflow_units'];candidates=[{'iteration':int(m[1]),'cpd_ns':float(m[2]),'admissible':bool(int(m[3]))} for m in re.finditer(r'ROUTECAST_INCUMBENT_CANDIDATE iter=(\d+) cpd_ns=([0-9.e+-]+) admissible=(\d+)',log)];results.append({'case':case,'pair_index':pair,'max_criticality':crit,'guard':guard,'seed_cpd_ns':row['cpd_ns'],'cpd_ns':cpd,'candidates':candidates,'cwd':str(cwd),'command':cmd,'files_sha256':{str(p):sha(p) for p in cwd.iterdir() if p.is_file()}});print(case,cpd,[x for x in candidates if not x['admissible']],flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'binary_sha256':sha(binary),'build_receipt_sha256':sha(build/'receipt.json'),'parent_verification_sha256':sha(parent/'verification.json'),'source_sha256':sha(Path(__file__)),'scope':'Fresh-process guard-on/off all-NET repair on four preselected cases, including max_criticality0 stress. Not a production transaction, full synchronized bundle publication, hold/total PPA guarantee, cold-quality or speedup claim.'},indent=2)+'\n')
