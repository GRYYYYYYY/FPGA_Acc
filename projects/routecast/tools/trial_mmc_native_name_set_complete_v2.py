"""Rerun unchanged complete native XML auditor with indexed name membership."""
import json,sys,subprocess,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_native_name_set_complete_v2_2026-10-08'
W=R/'experiments/ultraembedded_mmc_continuous_workflow_v4_2026-10-08'
P=R/'experiments/native_endpoint_name_set_v1_2026-10-08/independent_verification_v1.json'
proof=json.loads(P.read_text());assert proof['complete_counter_and_exact_source_change_pass']
assert all(sha(p)==h for p,h in proof['bindings'].items())
source=R/'tools/verify_ultraembedded_mmc_native_name_set_v2.py'
bindings={**closure([Path(__file__),source]),str(P):sha(P)}
D.mkdir(exist_ok=False);rows=[];adapters={}
for arm in ['cold','seed']:
 original=W/arm/'native/mmc';out=D/arm/'mmc';out.mkdir(parents=True)
 for f in ['receipt.json','output.route','native.log']:
  p=original/f;bindings[str(p)]=sha(p);shutil.copyfile(p,out/f);assert sha(out/f)==sha(p)
 for f in ['physical_audit.json','verification.json']:
  p=original/f;bindings[str(p)]=sha(p)
 code=source.read_text().replace('R=Path(__file__).resolve().parents[1]',f'R=Path({str(R)!r})')
 code=code.replace('ultraembedded_mmc_native_cold_v1_2026-10-08',str((D/arm).relative_to(R/'experiments')))
 code=code.replace('ultraembedded_mmc_native_demand_v1_2026-10-08',str((W/arm/'demand').relative_to(R/'experiments')))
 adapter=D/f'{arm}_adapter.py';adapter.write_text(code);bindings[str(adapter)]=sha(adapter);adapters[arm]=adapter
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Both complete archived MMC native routes, original XML streaming arcs/switches/parents/capacity audit and original FULL log checks. Only endpoint-name set placement changed. Fresh audit, no new native routing; single candidate clocks not paired performance or full workflow proof.'),indent=2)+'\n')
for arm in ['cold','seed']:
 assert all(sha(p)==h for p,h in bindings.items())
 with (D/f'{arm}.log').open('w') as log:
  tick=time.perf_counter();run=subprocess.run([sys.executable,str(adapters[arm]),'mmc'],cwd=R,stdout=log,stderr=subprocess.STDOUT);seconds=time.perf_counter()-tick
 if run.returncode:
  (D/'failure.json').write_text(json.dumps(dict(arm=arm,exit_code=run.returncode))+'\n');raise SystemExit(run.returncode)
 out=D/arm/'mmc';original=W/arm/'native/mmc'
 assert (out/'physical_audit.json').read_bytes()==(original/'physical_audit.json').read_bytes()
 result=json.loads((out/'verification.json').read_text())
 assert all(sha(p)==h for p,h in result['bindings'].items())
 assert result['physical_connections']==115572 and result['overflow_units']==0
 rows.append(dict(arm=arm,complete_physical_audit_bytes_equal=True,seconds=seconds,proof_sha256=sha(out/'verification.json')))
 print(json.dumps(rows[-1]),flush=True)
 (D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n')
