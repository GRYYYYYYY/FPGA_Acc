"""Malformed seed subprocess rejection tests; not in-memory rollback evidence."""
import json,re,shutil,subprocess,os
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_seed_rejection_2026-10-06';work=root/'work/native_seed_rejection_2026-10-06';out.mkdir();work.mkdir();src=root/'work/native_search_seed_v3_2026-10-06';cmd=json.loads((root/'experiments/native_search_seed_v3_2026-10-06/command.json').read_text())['command'];cmd[0]=str(root/'build/native_search_seed_timing_v4_2026-10-06/routecast_search_seed_vpr');original=(src/'seed.route').read_text();cases={}
cases['stale_digest']=re.sub(r'Placement_ID:\s*\S+','Placement_ID: SHA256:'+'0'*64,original,count=1)
cases['out_of_range_pin']=re.sub(r'Net_pin_index:\s*\d+','Net_pin_index: 999999',original,count=1)
cases['duplicate_pin']=original.replace('Net_pin_index: 2','Net_pin_index: 1',1)
# First source remains a valid SOURCE RR node but belongs to another physical terminal.
cases['wrong_source']=re.sub(r'Node:\s*1696\s+SOURCE[^\n]*','Node: 348 SOURCE (1,2,0) Class: 6 Switch: 0',original,count=1);assert cases['wrong_source']!=original
results=[]
for name,text in cases.items():
 cwd=work/name;cwd.mkdir();case=out/name;case.mkdir()
 for f in ('design.blif','design.net','design.place'):shutil.copyfile(src/f,cwd/f)
 (cwd/'seed.route').write_text(text);files=[cwd/f for f in ('design.blif','design.net','design.place','seed.route')];before={str(p):sha(p) for p in files};env=os.environ.copy();env['ROUTECAST_NATIVE_SEED']=str(cwd/'seed.route');(case/'command.json').write_text(json.dumps({'command':cmd,'cwd':str(cwd),'input_sha256':before},indent=2)+'\n')
 with (case/'run.log').open('w') as log:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
 log=(case/'run.log').read_text();assert code!=0 and 'VPR succeeded' not in log;assert all(sha(p)==h for p,h in before.items());assert not (cwd/'output.route').exists();result={'case':name,'exit_code':code,'input_files_unchanged':True,'no_published_route':True,'log_sha256':sha(case/'run.log'),'tail':log[-1600:]};results.append(result);print(name,code,flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'source_sha256':sha(__file__),'binary_sha256':sha(cmd[0]),'scope':'Private-process invalid input rejection and immutable input evidence. Not native in-process state rollback or formal atomic publication.'},indent=2)+'\n')
