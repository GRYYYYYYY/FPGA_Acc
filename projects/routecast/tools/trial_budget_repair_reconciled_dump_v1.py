"""Archived diagnosis: original sync plus post-sync physical route export."""
import json,os,shutil,subprocess
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/budget_repair_native_reload_v1_2026-10-08';p=json.loads((S/'protocol.json').read_text());assert all(sha(f)==h for f,h in p['inputs'].items())
B=R/'build/native_reconciled_dump_v1_2026-10-08';b=json.loads((B/'receipt.json').read_text());binary=B/'verbose_sync_vpr';assert sha(binary)==b['binary_sha256'] and all(sha(f)==h for f,h in b['bindings'].items())
D=R/'experiments/budget_repair_reconciled_dump_v1_2026-10-08';D.mkdir(exist_ok=False);inputs={str(S/'protocol.json'):sha(S/'protocol.json'),str(B/'receipt.json'):sha(B/'receipt.json'),str(binary):sha(binary),str(Path(__file__)):sha(Path(__file__))}
for n in ('design.blif','design.net','design.place','design.route'):
 f=S/n;inputs[str(f)]=sha(f);shutil.copyfile(f,D/n)
cmd=[str(binary),*p['command'][1:]];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
(D/'protocol.json').write_text(json.dumps(dict(inputs=inputs,command=cmd),indent=2)+'\n')
with (D/'reload.log').open('w') as f:code=subprocess.run(cmd,cwd=D,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
assert all(sha(f)==h for f,h in inputs.items());dump=D/'reconciled.route'
(D/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(D/'protocol.json'),exit_code=code,dump_sha256=sha(dump) if dump.exists() else None,files={str(f):sha(f) for f in D.iterdir() if f.is_file()}),indent=2)+'\n');print('native exit',code,'dump exists',dump.exists())
