"""Fixed ABBA fresh-process full12 audit observation, provided native archives."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/alternating_inventory_audit_v1_2026-10-08';D.mkdir(exist_ok=False)
order=['separate','unified','unified','separate']
sources=[Path(__file__),*[R/'tools'/f'run_{a}_inventory_cohort_audit_v1.py' for a in set(order)],*[R/'tools'/n for n in ('stream_native_route_audit_cached.py','stream_native_route_audit_unified_v1.py','memoized_fraction_path_delay_v1.py','memoized_fraction_path_delay_unified_v1.py','unified_rr_audit_inventory_v1.py','native_route_audit_cache.py','buffered_rc_node_classes.py','path_rc.py','pre_route_endpoints.py','native_route_ledger_import_compact.py','audit_native_route.py')]]
protocol=dict(order=order,bindings={str(p):sha(p) for p in sources},scope='ABBA fixed sequence, two fresh processes per arm, all12 archived routes, no native rerun. Complete subprocess clocks include startup/import/initial binding validation/audit/output/shutdown. OS filesystem cache not flushed, host contention not controlled.')
(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
rows=[]
for i,arm in enumerate(order):
 out=D/f'{i}_{arm}';cmd=[sys.executable,str(R/'tools'/f'run_{arm}_inventory_cohort_audit_v1.py'),str(out)]
 start=time.perf_counter()
 with (D/f'{i}_{arm}.log').open('x') as log:code=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 seconds=time.perf_counter()-start
 assert code==0
 v=json.loads((out/'verification.json').read_text())
 row=dict(index=i,arm=arm,command=cmd,exit_code=code,subprocess_seconds=seconds,audit_component_seconds=v['audit_component_seconds'],verification_sha256=sha(out/'verification.json'))
 rows.append(row);print(row,flush=True)
assert all(sha(p)==h for p,h in protocol['bindings'].items())
(D/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(D/'protocol.json'),rows=rows),indent=2)+'\n')
