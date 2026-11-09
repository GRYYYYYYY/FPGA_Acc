"""Frozen temporal induction screen; results are scoped to actual proof log."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/sha1_frontend_readiness_v1_2026-10-10';r=json.loads((S/'receipt.json').read_text());assert r['exit_code']==0 and all(sha(k)==v for k,v in r['bindings'].items())
Y=next(Path(k) for k in r['bindings'] if Path(k).name=='yosys');D=R/'experiments/sha1_frontend_equivalence_v1_2026-10-10';assert not D.exists();D.mkdir()
s='read_verilog '+str(S/'design.v')+'\nhierarchy -check -top sha1\nproc\nflatten\nmemory\nopt\ncheck -assert\nequiv_opt -assert -undef synth -top sha1 -flatten -lut 6\n'
(D/'check.ys').write_text(s);bindings={**r['bindings'],**{str(p):sha(p) for p in [Path(__file__).resolve(),S/'receipt.json',D/'check.ys']}}
plan=dict(bindings=bindings,command=[str(Y),'-s','check.ys'],timeout_s=120,scope='Original source elaboration lowered through proc/memory/opt versus synthesized form temporal induction only. No archived JSON/BLIF equivalence, routing, timing or heldout proof.')
(D/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');tick=time.perf_counter()
with (D/'equivalence.log').open('w') as log:
 try:code=subprocess.run(plan['command'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
 except subprocess.TimeoutExpired:code=124
text=(D/'equivalence.log').read_text();out=dict(exit_code=code,seconds=time.perf_counter()-tick,all_equiv_cells_proven_log='Equivalence successfully proven!' in text,scope=plan['scope'])
for p in D.iterdir():
 if p.is_file():bindings[str(p)]=sha(p)
assert all(sha(k)==v for k,v in bindings.items());out['bindings']=bindings
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
