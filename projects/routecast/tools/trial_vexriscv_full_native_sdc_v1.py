"""Actual native SDC binding using exit-before-pack; preserves ongoing baseline pack."""
import json,hashlib,subprocess,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'vexriscv_full_native_sdc_v1_2026-10-09';D.mkdir(exist_ok=False);B=E/'vexriscv_full_native_pack_v1_2026-10-09';plan=json.loads((B/'protocol.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,h in plan['bindings'].items():assert sha(p)==h
S=E/'vexriscv_full_development_sdc_v1_2026-10-09';source=E/'vexriscv_full_mapped_structure_v1_2026-10-09/design.blif';shutil.copyfile(source,D/'design.blif');shutil.copyfile(S/'development.sdc',D/'development.sdc');cmd=plan['command']+['--sdc_file','development.sdc','--exit_before_pack','on'];paths=[Path(__file__).resolve(),B/'protocol.json',source,S/'protocol.json',S/'development.sdc',D/'design.blif',D/'development.sdc',Path(cmd[0]),Path(cmd[1])];bindings={str(p):sha(p) for p in paths};(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=cmd,timeout_s=60,scope='Fresh development-SDC parser/clock binding only, exit before packing; not routed STA/timing pass or prediction labels.'),indent=2)+'\n');start=time.perf_counter()
with (D/'native.log').open('x') as log:
 try:code=subprocess.run(cmd,cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,exit_code=code,seconds=time.perf_counter()-start,files={str(p):sha(p) for p in D.iterdir() if p.is_file()},admitted_for_prediction=False),indent=2)+'\n');print('exit',code)
