"""Complete snapshot model/whole-NET selection/pin serialization plus fresh full3audits."""
import json,sys,time,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_native_snapshot_exact_handoff_v1_2026-10-10';assert not D.exists();D.mkdir();ep=R/'experiments/sha_second_swap_overflow_guard_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json';driver=R/'tools/run_sha_native_snapshot_exact_guard_handoff_v1.py';audit=R/'tools/run_shared_overflow_guard_audits_v1.py';bindings=closure([Path(__file__),driver,audit]);bindings[str(ep)]=sha(ep);commands=[[sys.executable,str(driver),'sha1',str(ep),str(D/'handoff'),str(D/'native'),str(D/'model')],[sys.executable,str(audit),str(D/'model'),'sha1']];(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,commands=commands,scope='Complete local snapshot parsing/authentication/exact model/current graph adapter/wholeNET selection/native pinbinding+seed serialization/fresh3originalXML audits. Prior native snapshot generation/staticmetadata preparation excluded and retained separately; not inprocess/zero-copy/fullnative/canonical netgain.'),indent=2)+'\n');tick=time.perf_counter();rows=[]
for stage,cmd in enumerate(commands):
 begin=time.perf_counter()
 with (D/f'stage{stage}.log').open('w') as log:code=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=1200).returncode
 rows.append(dict(stage=stage,exit_code=code,seconds=time.perf_counter()-begin));(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');assert code==0
assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,complete_model_handoff_audits_seconds=time.perf_counter()-tick),indent=2)+'\n');print('COMPLETE SNAPSHOT HANDOFF+AUDITS',rows)
