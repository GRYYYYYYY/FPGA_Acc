"""Startup-contract witness with initialization controls unconstrained."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'ram_initial_control_counterexample_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'ram_word_relation_v1_2026-10-09';r=json.loads((B/'receipt.json').read_text());assert r['passed']
for p,h in {**r['bindings'],**r['files']}.items():assert sha(p)==h
y=Path(next(p for p in r['bindings'] if p.endswith('/bin/yosys')))
s=(B/'relation.v').read_text();assert "wire pw=1'b0,er=1'b0;" in s
s=s.replace('input [9:0] tracked,pa,input [19:0] pd,raw,fwd,input hit,output bad);','input [9:0] tracked,pa,input [19:0] pd,raw,fwd,input hit,pw,er,output bad);').replace("wire pw=1'b0,er=1'b0;",'// Startup controls unconstrained only for this admission counterexample.')
(D/'miter.v').write_text(s);(D/'check.ys').write_text('read_verilog miter.v\nhierarchy -check -top initial_relation\nproc\nflatten\nopt\ncheck -assert\nsat -prove bad 0 -show-inputs -show bad\n')
bindings={str(p):sha(p) for p in [Path(__file__),B/'receipt.json',B/'relation.v',y,D/'miter.v',D/'check.ys']}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,timeout_s=60,scope='Counterexample to matched arbitrary startup contract when pw/er initialization is unconstrained; same prior symbolic relation. Not proof physical device omits init, actual wrapper failure, four-state or Full sequential equivalence.'),indent=2)+'\n')
with (D/'check.log').open('x') as log:
 try:code=subprocess.run([str(y),'-s','check.ys'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
found=code==0 and 'model found: FAIL' in (D/'check.log').read_text();assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(counterexample_found=found,exit_code=code,bindings=bindings,log_sha256=sha(D/'check.log'),scope='Initialization is a necessary gate; existential witness does not show actual configured hardware fails.'),indent=2)+'\n');print('counterexample_found',found);assert found
