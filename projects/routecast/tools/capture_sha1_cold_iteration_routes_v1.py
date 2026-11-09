"""Separate diagnostic snapshot run; never used as complete timing trial."""
import json,os,subprocess,shutil,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];src=R/'experiments/sha1_actual_old_linear_expat_workflow_v1_2026-10-10';v=json.loads((src/'verification.json').read_text());assert v['all_cases_both_complete_arms_authenticated'];assert all(sha(k)==h for k,h in v['bindings'].items())
native=src/'cold/native/sha1';r=json.loads((native/'receipt.json').read_text());cmd=r['command']+['--save_routing_per_iteration','on'];D=R/'experiments/sha1_cold_iteration_routes_v1_2026-10-10';D.mkdir();bindings={str(Path(__file__)):sha(Path(__file__)),str(src/'verification.json'):sha(src/'verification.json'),str(native/'receipt.json'):sha(native/'receipt.json')}
for f in ['design.blif','design.net','design.place']:shutil.copyfile(native/f,D/f);bindings[str(native/f)]=sha(native/f);bindings[str(D/f)]=sha(D/f)
for p in [Path(cmd[0]),Path(cmd[1]),Path(cmd[cmd.index('--read_rr_graph')+1])]:bindings[str(p)]=sha(p)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=cmd,scope='Separate width128 cold diagnostic snapshots, unchanged inputs/router settings plus save flag only. Prior outcomes known. No reuse as uninstrumented wall-time observation, family heldout or failure label. Every snapshot must be audited before spatial use.'),indent=2)+'\n')
t=time.perf_counter()
with (D/'native.log').open('w') as log:code=subprocess.run(cmd,cwd=D,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=1200).returncode
snapshots=sorted(D.glob('iteration_*.route'));assert code==0 and 'VPR succeeded' in (D/'native.log').read_text() and snapshots
assert all(sha(k)==h for k,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,exit_code=code,instrumented_process_seconds=time.perf_counter()-t,files={str(p):sha(p) for p in D.iterdir() if p.is_file()},snapshots=[str(p) for p in snapshots],snapshot_audit_pass=False),indent=2)+'\n')
print('SNAPSHOT CAPTURE',len(snapshots))
