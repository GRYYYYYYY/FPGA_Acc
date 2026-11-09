"""Reject malformed units/header and incomplete endpoint coverage in private native loader."""
import json,os,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'experiments/native_resume_indfloor_v2_w16_m1_cold_2026-10-07';r=json.loads((base/'receipt.json').read_text());native=next(s['native'] for s in r['stages'] if 'native' in s);original=(base/'rr_floors.txt').read_text().splitlines();out=ROOT/'experiments/native_resume_indfloor_loader_contract_2026-10-07';out.mkdir(exist_ok=False);rows=[]
for name in ('wrong_units','wrong_node_count','missing_pair'):
 work=out/name;work.mkdir();lines=list(original);header=lines[0].split()
 if name=='wrong_units':header[0]='ROUTECAST_FLOORS_NANOSECONDS_V1'
 elif name=='wrong_node_count':header[2]=str(int(header[2])+1)
 else:lines.pop();header[3]=str(int(header[3])-1)
 lines[0]=' '.join(header);floor=work/'floors.txt';floor.write_text('\n'.join(lines)+'\n')
 for f in ('design.blif','design.net','design.place'):shutil.copyfile(base/'first'/f,work/f)
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_RR_FLOORS_FILE']=str(floor)
 with (work/'run.log').open('w') as stream:code=subprocess.run(native['command'],cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=60).returncode
 text=(work/'run.log').read_text();assert code!=0 and 'VPR succeeded' not in text
 expected='floor endpoint coverage mismatch' if name=='missing_pair' else 'floor header mismatch';assert expected in text
 rows.append(dict(case=name,exit_code=code,error=expected,files={str(f):sha(f) for f in work.iterdir() if f.is_file()}));print(name,code,flush=True)
(out/'verification.json').write_text(json.dumps(dict(rows=rows,source_sha256=sha(Path(__file__)),original_receipt_sha256=sha(base/'receipt.json'),scope='Private native loader rejects three header/coverage failures. Launcher binds cryptographic graph digest; native loader does not independently check digest content. No complete parser fuzzing.'),indent=2)+'\n')
