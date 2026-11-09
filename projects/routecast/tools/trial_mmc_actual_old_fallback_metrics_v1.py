"""Run complete post-admission development metrics and both frozen controls."""
import json,sys,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_actual_old_fallback_metrics_execution_v1_2026-10-09';assert not D.exists()
admission=R/'experiments/mmc_actual_old_joint_fallback_v10_2026-10-09/verification.json'
r=json.loads(admission.read_text());assert r['complete_online_feedback_physical_and_actual_old_fallback_events_pass']
bindings={str(admission):sha(admission)}
for p,h in r['bindings'].items():assert sha(p)==h;bindings[p]=h
steps=[('evaluate_mmc_actual_old_fallback_hotspots_v4.py',['mmc']),('verify_mmc_actual_old_fallback_hotspots_v4.py',['mmc']),('audit_mmc_actual_old_fallback_hotspot_ties_v3.py',[]),('compare_mmc_actual_old_fallback_vs_linear_metrics_v1.py',[]),('compare_mmc_actual_old_fallback_vs_triangular_metrics_v1.py',[]),('compare_mmc_fallback_online_models_v1.py',[])]
bindings.update(closure([Path(__file__),*[R/'tools'/s for s,_ in steps]]))
D.mkdir();(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy='Post-outcome development evaluation only after full online admission. Same full cold labels, resource/spatial universe, fixed k/ties, numerical verification and two controls; no fitting or candidate changes.'),indent=2)+'\n')
stages=[];begin=time.perf_counter()
for i,(script,args) in enumerate(steps):
 print('START',i,script,flush=True);log=D/f'stage{i}.log';tick=time.perf_counter()
 with log.open('w') as f:result=subprocess.run([sys.executable,str(R/'tools'/script),*args],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
 stages.append(dict(stage=i,script=script,exit_code=result.returncode,seconds=time.perf_counter()-tick,log=str(log)));(D/'stages.json').write_text(json.dumps(stages,indent=2)+'\n');print('END',i,result.returncode,flush=True)
 if result.returncode:sys.exit(result.returncode)
assert all(sha(p)==h for p,h in bindings.items())
metrics=R/'experiments/mmc_actual_old_fallback_hotspots_v4_2026-10-09/mmc'
files={str(p):sha(p) for p in [D/'stages.json',metrics/'comparison.json',metrics/'metric_verification.json',metrics/'truth_tie_sensitivity.json',R/'experiments/mmc_actual_old_fallback_vs_linear_metrics_v1_2026-10-09/comparison.json',R/'experiments/mmc_actual_old_fallback_vs_triangular_metrics_v1_2026-10-09/comparison.json',R/'experiments/mmc_fallback_online_comparison_v1_2026-10-09/comparison.json']}
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,files=files,complete_metrics_and_two_control_comparisons_pass=True,seconds=time.perf_counter()-begin,scope='Descriptive development metrics only; not prospective/heldout/native QoR/full workflow timing proof.'),indent=2)+'\n');print('COMPLETE authenticated full metrics and two controls',flush=True)
