"""Batched input framing/selection rejection on authentic graph payload."""
import sys,json,struct,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/native_budget_batch_contract_2026-10-07';out.mkdir();source=R/'experiments/native_budget_batch_parity_2026-10-07/step_3/batch.bin';raw=source.read_bytes();magic,n,m,k,q,budget=struct.unpack_from('<6Q',raw);assert q>=2;binary=R/'build/native_resume_budget_batch_cpp_2026-10-07/budget_batch';duplicate=bytearray(raw);last=len(raw)-8*q;duplicate[last+8:last+16]=duplicate[last:last+8];cases=[('truncated',raw[:-1],'truncated'),('trailing',raw+b'x','trailing'),('magic',b'\0'*8+raw[8:],'magic'),('duplicate_selection',duplicate,'selection')];rows=[]
for name,data,error in cases:
 p=out/(name+'.bin');p.write_bytes(data);r=subprocess.run([str(binary),str(p)],capture_output=True,timeout=20);assert r.returncode==2 and r.stderr.decode().strip()==error;rows.append(dict(case=name,error=error,payload_sha256=sha(p)))
(out/'receipt.json').write_text(json.dumps(dict(rows=rows,source_sha256=sha(source),binary_sha256=sha(binary),checker_sha256=sha(__file__)),indent=2)+'\n');print('PASS',len(rows))
