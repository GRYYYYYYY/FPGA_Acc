"""All-output partitioned CEC diagnosis after monolithic explicit TIMEOUT."""
import json,hashlib,subprocess,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'vexriscv_full_cut_mapping_v1_2026-10-09';D=E/'vexriscv_full_partitioned_cec_v1_2026-10-09';D.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();r=json.loads((B/'receipt.json').read_text());assert r['results'][0]['exit_code']==0 and r['results'][1]['exit_code']=='TIMEOUT'
for p,h in {**r['bindings'],**r['files']}.items():assert sha(p)==h
abc=json.loads((B/'protocol.json').read_text())['abc'];paths=[Path(__file__).resolve(),B/'receipt.json',B/'original.blif',B/'mapped.blif',E/'vexriscv_full_cec_diagnosis_v1_2026-10-09/help.log',Path(abc)]
for name in ('original.blif','mapped.blif'):shutil.copyfile(B/name,D/name);paths.append(D/name)
bindings={str(p):sha(p) for p in paths};command=[abc,'-c','cec -p -P 512 original.blif mapped.blif'];(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=command,timeout_s=180,scope='All original outputs, ABC native partitioning512, same networks/binary and wall budget after monolithic timeout; no output subsampling or mapped network changes.'),indent=2)+'\n');start=time.perf_counter()
with (D/'cec.log').open('x') as log:
 try:code=subprocess.run(command,cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
passed=code==0 and 'Networks are equivalent' in (D/'cec.log').read_text();(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,exit_code=code,seconds=time.perf_counter()-start,passed=passed,admitted_for_prediction=False,files={str(p):sha(p) for p in D.iterdir() if p.is_file()}),indent=2)+'\n');print(code,passed)
