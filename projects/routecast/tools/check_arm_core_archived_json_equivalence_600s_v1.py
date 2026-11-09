"""Frozen temporal induction screen; results are scoped to actual proof log."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/routecast');S=R/'experiments/verilog_frontend_cohort_v3_2026-10-10/arm_core';r=json.loads((S/'receipt.json').read_text());assert r['exit_code']==0 and all(sha(k)==v for k,v in r['bindings'].items())
Y=next(Path(k) for k in r['bindings'] if Path(k).name=='yosys');D=R/'experiments/arm_core_archived_json_equivalence_600s_v1_2026-10-10';assert not D.exists();D.mkdir()
s='read_verilog '+str(S/'design.v')+'\nhierarchy -check -top arm_core\nproc\nflatten\nmemory\nopt\ncheck -assert\ndesign -stash source_gold\nread_json '+str(S/'design.json')+'\nrename arm_core gate\ndesign -stash archived_gate\ndesign -copy-from source_gold -as gold arm_core\ndesign -copy-from archived_gate -as gate gate\nequiv_make gold gate equiv\nhierarchy -check -top equiv\nequiv_simple -undef\nequiv_induct -undef\nequiv_status -assert\n'
(D/'check.ys').write_text(s);bindings={**r['bindings'],**{str(p):sha(p) for p in [Path(__file__).resolve(),S/'receipt.json',D/'check.ys']}}
plan=dict(bindings=bindings,command=[str(Y),'-s','check.ys'],timeout_s=600,scope='Original lowered source versus exact archived JSON using complete equiv points. Temporal induction limitations and initial synchronization remain; serialized BLIF structure separate, no native/timing/heldout proof.')
(D/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');tick=time.perf_counter()
with (D/'equivalence.log').open('w') as log:
 try:code=subprocess.run(plan['command'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
 except subprocess.TimeoutExpired:code=124
text=(D/'equivalence.log').read_text();out=dict(exit_code=code,seconds=time.perf_counter()-tick,all_equiv_cells_proven_log='Equivalence successfully proven!' in text,scope=plan['scope'])
for p in D.iterdir():
 if p.is_file():bindings[str(p)]=sha(p)
assert all(sha(k)==v for k,v in bindings.items());out['bindings']=bindings
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
