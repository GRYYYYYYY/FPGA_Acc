"""Frozen source-declared SHA160 frontend screen; no route labels or heldout admission."""
import json,shutil,subprocess,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
S=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/benchmarks/verilog'
D=R/'experiments/sha1_frontend_readiness_v1_2026-10-10';assert not D.exists()
prior=R/'experiments/vexriscv_smallest_frontend_candidate_2026-10-06/protocol.json';yp=json.loads(prior.read_text())['yosys'];Y=Path(yp['yosys_path']);assert sha(Y)==yp['sha256']
source=S/'sha.v';bindings={str(p):sha(p) for p in [Path(__file__).resolve(),Y,prior,source]}
D.mkdir();shutil.copyfile(source,D/'design.v')
script='read_verilog design.v\nhierarchy -check -top sha1\nsynth -top sha1 -flatten -lut 6\ndffunmap\ncheck -assert\nstat\nwrite_json design.json\nwrite_blif design.blif\n'
(D/'synth.ys').write_text(script)
for p in [D/'design.v',D/'synth.ys']:bindings[str(p)]=sha(p)
plan=dict(bindings=bindings,selection='source-local origin declaration and single explicit top; no route outcomes used',candidate='sha1',family_scope='SHA160 origin and cryptographic-domain overlap unresolved; no heldout claim',command=[str(Y),'-s','synth.ys'],timeout_s=600,heldout_admitted=False,scope='Frontend type/width screen only. No reset stripping/async2sync, source equivalence, native/architecture timing or route-label evidence.')
(D/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');tick=time.perf_counter()
with (D/'synthesis.log').open('w') as log:
 try:code=subprocess.run(plan['command'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
 except subprocess.TimeoutExpired:code=124
out=dict(exit_code=code,seconds=time.perf_counter()-tick,heldout_admitted=False)
if code==0:
 net=json.loads((D/'design.json').read_text());assert set(net['modules'])=={'sha1'};cells=net['modules']['sha1']['cells'];types=Counter(c['type'] for c in cells.values());assert all(int(c['parameters']['WIDTH'],2)<=6 for c in cells.values() if c['type']=='$lut')
 out.update(cell_types=dict(types),unsupported_for_existing_boolean_schema={k:v for k,v in types.items() if k not in ['$_MUX_','$_XOR_','$_XNOR_','$_NOT_','$_OR_','$_AND_','$_DFF_P_','$_DFF_PP0_','$_DFF_PP1_','$scopeinfo']})
for p in D.iterdir():
 if p.is_file():bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
out.update(bindings=bindings,scope=plan['scope']);(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2),flush=True)
