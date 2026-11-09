"""Frozen temporal induction screen; results are scoped to actual proof log."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/sha1_frontend_readiness_v1_2026-10-10';r=json.loads((S/'receipt.json').read_text());assert r['exit_code']==0 and all(sha(k)==v for k,v in r['bindings'].items())
Y=next(Path(k) for k in r['bindings'] if Path(k).name=='yosys');D=R/'experiments/sha1_reset_alignment_sat_v1_2026-10-10';assert not D.exists();D.mkdir()
s='read_verilog '+str(S/'design.v')+'\nhierarchy -check -top sha1\nproc\nflatten\nmemory\nopt\ncheck -assert\ndesign -stash source_gold\nread_json '+str(S/'design.json')+'\nrename sha1 gate\ndesign -stash archived_gate\ndesign -copy-from source_gold -as gold sha1\ndesign -copy-from archived_gate -as gate gate\nmiter -equiv -make_outputs gold gate miter\nhierarchy -check -top miter\nflatten\nopt_clean\nsat -seq 6 -set-at 1 in_rst_i 1 -set-at 2 in_rst_i 1 -set-at 3 in_rst_i 0 -set-at 4 in_rst_i 0 -set-at 5 in_rst_i 0 -set-at 6 in_rst_i 0 -prove trigger 0 -prove-skip 2 -verify -show-inputs -show-outputs\n'
(D/'check.ys').write_text(s);bindings={**r['bindings'],**{str(p):sha(p) for p in [Path(__file__).resolve(),S/'receipt.json',D/'check.ys']}}
plan=dict(bindings=bindings,command=[str(Y),'-s','check.ys'],timeout_s=120,scope='Bounded six symbolic clock steps, reset asserted first two then deasserted, all other inputs unconstrained; output trigger equality only after skip2. Independent arbitrary initial states. Not unbounded reset/source/crypto/timing/heldout proof.')
(D/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');tick=time.perf_counter()
with (D/'equivalence.log').open('w') as log:
 try:code=subprocess.run(plan['command'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
 except subprocess.TimeoutExpired:code=124
text=(D/'equivalence.log').read_text();out=dict(exit_code=code,seconds=time.perf_counter()-tick,reset_alignment_sat_success='SAT proof finished - no model found: SUCCESS!' in text,scope=plan['scope'])
for p in D.iterdir():
 if p.is_file():bindings[str(p)]=sha(p)
assert all(sha(k)==v for k,v in bindings.items());out['bindings']=bindings
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
