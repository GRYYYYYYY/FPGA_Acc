"""Frozen monotonic-overflow acceptance prototype, full development layouts and independent certificates."""
import json,sys,subprocess,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_overflow_guard_v1_2026-10-10';assert not D.exists();D.mkdir();model=R/'tools/run_resident_overflow_guard_model_v1.py';audit=R/'tools/run_shared_overflow_guard_audits_v1.py';bindings=closure([Path(__file__),model,audit]);cases=[('original',R/'experiments/sha1_compact_json_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json'),('second_swap',R/'experiments/sha_second_swap_complete_workflow_v1_2026-10-10/cold/demand/sha1/endpoints.json')];bindings.update({str(p):sha(p) for _,p in cases});(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=[(c,str(p)) for c,p in cases],scope='Freeze nonincreasing prospective fullgraph overflow guard before new runs. Original fixedprices/two rounds/search/fallback/6273queries retained. Reject entire candidate, retain full rejected paths/budgets/epoch. Exposeddevelopment diagnostic only, no label-fitted threshold/best-arm/native or fullwalltime claim.'),indent=2)+'\n');rows=[]
for case,ep in cases:
 W=D/case;W.mkdir();tick=time.perf_counter();codes=[]
 for stage,cmd in [('model',[sys.executable,str(model),str(ep),str(W/'model')]),('audit',[sys.executable,str(audit),str(W/'model'),'sha1'])]:
  with (W/(stage+'.log')).open('w') as log:code=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=1200).returncode
  codes.append(code)
  if code:break
 row=dict(case=case,codes=codes,complete_model_and_audits_seconds=time.perf_counter()-tick);rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(row,flush=True)
 if codes!=[0,0]:break
assert len(rows)==2 and all(x['codes']==[0,0] for x in rows) and all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_complete_models_and_audits_pass=True),indent=2)+'\n')
