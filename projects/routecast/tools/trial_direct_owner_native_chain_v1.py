"""Prospective clock for actual serialization, native reload, canonical and audits."""
import json
import subprocess
import time
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
D=R/'experiments/direct_owner_native_chain_v1_2026-10-08'
D.mkdir(exist_ok=False)
names=('trial_direct_owner_native_reload_v1.py','verify_direct_owner_native_dump_v1.py','trial_direct_owner_canonical_v1.py','verify_direct_owner_canonical_v1.py','verify_direct_owner_native_quality_v1.py')
source=R/'experiments/direct_owner_global_wire_v1_2026-10-08/verification.json'
proof=json.loads(source.read_text())
assert proof['all1929_events_and_complete_original_xml_fraction_frame_pass'] and proof['all_dynamic_model_guards_pass']
assert all(sha(p)==h for p,h in proof['bindings'].items())
bindings={str(source):sha(source),str(Path(__file__)):sha(Path(__file__))}
for name in names:bindings[str(R/'tools'/name)]=sha(R/'tools'/name)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,stages=names,
 scope='From provided independently verified direct-single-pass fresh candidate: actual serialization/native FULL STA/post-sync audit/canonical reload, audit and quality comparison. Includes process startup and stage JSON output. Excludes producing candidate/upstream route and final chain receipt write; single component observation, not end-to-end speedup.'),indent=2)+'\n')
started=time.perf_counter();stages=[]
for name in names:
 tick=time.perf_counter()
 with (D/(name+'.log')).open('w') as log:
  code=subprocess.run(['python3',str(R/'tools'/name)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 stages.append(dict(script=name,exit_code=code,elapsed_seconds=time.perf_counter()-tick))
 (D/'progress.json').write_text(json.dumps(stages,indent=2)+'\n')
 print(stages[-1],flush=True)
 if code:raise RuntimeError('stage failed: '+name)
elapsed=time.perf_counter()-started
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,protocol_sha256=sha(D/'protocol.json'),
 stages=stages,component_elapsed_seconds=elapsed,full_workflow_seconds=None),indent=2)+'\n')
print('native acceptance chain terminal',elapsed,flush=True)
