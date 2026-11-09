"""Demonstrate --route does not parse a preexisting --route_file as seed."""
import json,os,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
prior=ROOT/'experiments/mux32_old_placement_cold_control_2026-10-07'
r=json.loads((prior/'receipt.json').read_text());p=json.loads((prior/'protocol.json').read_text())
assert r['protocol_sha256']==sha(prior/'protocol.json')
assert all(sha(f)==h for f,h in {**p['inputs'],**p['sources'],**r['files']}.items())
out=ROOT/'experiments/native_route_file_resume_semantics_2026-10-07';out.mkdir(exist_ok=False)
source=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128'
inputs={str(f):sha(f) for f in (source/'design.blif',source/'design.net',source/'design.place',Path(r['command'][0]),Path(r['command'][1]),source/'rr_graph.xml')}
for name in ('design.blif','design.net','design.place'):shutil.copyfile(source/name,out/name)
route=out/'output.route';route.write_text('ROUTECAST_INVALID_ROUTE_SEED_SENTINEL\n');seedhash=sha(route)
cmd=r['command'];protocol=dict(command=cmd,inputs=inputs,invalid_preexisting_route_sha256=seedhash,source_sha256=sha(Path(__file__)),scope='Isolated native CLI semantics check with unchanged old placement and deliberate invalid output path contents; no warm-start claim')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
start=time.perf_counter()
with (out/'run.log').open('w') as log:
 code=subprocess.run(cmd,cwd=out,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
elapsed=time.perf_counter()-start
text=(out/'run.log').read_text();assert code==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
assert sha(route)!=seedhash
norm=lambda f:{n:Counter(paths) for n,paths in physical_paths(f).items() if paths}
assert norm(route)==norm(prior/'output.route')
assert all(sha(f)==h for f,h in inputs.items())
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src'
sources=[shared/'base/vpr_api.cpp',shared/'base/read_options.cpp',shared/'route/route.cpp',shared/'route/route_common.cpp']
result=dict(protocol_sha256=sha(out/'protocol.json'),native_exit_code=code,native_subprocess_seconds=elapsed,invalid_existing_route_ignored=True,all_named_paths_equal_cold_control=True,inputs=inputs,upstream_sources={str(f):sha(f) for f in sources},files={str(f):sha(f) for f in (out/'run.log',route)},scope='--route computes route despite invalid preexisting --route_file; all paths reproduce previous cold control. --analysis/load is distinct. Does not disprove every possible API warm start, nor implement resumed/incremental routing. Native FULL runtime succeeded; no new canonical audit, timing netgain or heldout.')
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(code,elapsed,'invalid seed ignored; cold paths equal')
