"""Frozen 2x2 prices, full model and independent full-frame/event audits, both development layouts."""
import json,sys,subprocess,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_price_factorial_ablation_v2_2026-10-10';assert not D.exists();D.mkdir()
plans=[]
for case,ep in [('original','sha1_compact_json_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json'),('second_swap','sha_second_swap_complete_workflow_v1_2026-10-10/cold/demand/sha1/endpoints.json')]:
 for mode in ['both','no_span','no_overuse','neither']:
  model=R/'tools'/('run_resident_actual_old_linear_undo_model_v13.py' if mode=='both' else f'run_resident_price_ablation_{mode}_v1.py');audit=R/'tools'/('run_shared_actual_old_linear_direct_lattice_audits_v4.py' if mode=='both' else f'run_shared_price_ablation_{mode}_audits_v1.py')
  plans.append(dict(case=case,mode=mode,endpoint=str(R/'experiments'/ep),model=str(model),audit=str(audit)))
bindings=closure([Path(__file__),*[Path(p[k]) for p in plans for k in ['model','audit']]]);bindings.update({p['endpoint']:sha(p['endpoint']) for p in plans})
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,plans=plans,scope='Frozen complete2x2 span/overuse price ablation both exposed development SHA layouts. Preserve initialzero floors/budgets/full2rounds/all6273queries/wholeNET replacement/fallback and fulloriginalfirst-round CHAN schedule for everyfactor. Congestion node affected schedules remain data dependent. No label fitting/best-arm choice, no native/fullworkflow time claim.'),indent=2)+'\n');rows=[]
for p in plans:
 W=D/p['case']/p['mode'];W.mkdir(parents=True);tick=time.perf_counter();codes=[]
 for stage,cmd in [('model',[sys.executable,p['model'],p['endpoint'],str(W/'model')]),('audit',[sys.executable,p['audit'],str(W/'model'),'sha1'])]:
  with (W/(stage+'.log')).open('w') as log:code=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=1200).returncode
  codes.append(code)
  if code:break
 row=dict(**p,codes=codes,complete_model_audits_seconds=time.perf_counter()-tick);rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(row,flush=True)
 if codes!=[0,0]:break
assert len(rows)==8 and all(r['codes']==[0,0] for r in rows);assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all8complete_models_and_independent_audits_pass=True),indent=2)+'\n')
