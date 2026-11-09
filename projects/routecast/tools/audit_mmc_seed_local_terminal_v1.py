"""Audit completed local native output without rerunning seed routing."""
import json,sys,re,time,subprocess,resource,traceback
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
from audit_mmc_v16_native_iteration_work_v1 import parse
from shared_compact_native_inventory_v1 import Inventory
import canonical_reload_pin_index_expat_v3 as canonical
R=Path(__file__).resolve().parents[1]
D=R/'experiments/mmc_native_seed_utility_pilot_v1_2026-10-18'
O=D/'local_terminal_audit_v1';O.mkdir()
p=json.loads((D/'protocol.json').read_text())
assert all(sha(path)==h for path,h in p['bindings'].items())
src=D/'local';terminal=json.loads((src/'terminal.json').read_text());assert terminal['exit_status']==0 and not terminal['native_timeout']
log=(src/'native.log').read_text();assert all(x in log for x in ['VPR succeeded','Completed routing consistency check successfully.','NET-aware seed imported'])
row={**terminal,'wirelength':int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]),'diagnostic_cpd_ns':float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]),'native_work':parse(log)}
row['iterations']=row['native_work']['iterations']
cmd=p['commands']['local'];graph=Path(cmd[cmd.index('--read_rr_graph')+1])
epfile=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json';ep=json.loads(epfile.read_text())
for name in ['design.blif','design.net','design.place']:
 original=Path(ep['inputs']['net']['path']).parent/name
 assert sha(original)==sha(src/name),name
required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections'])
print('PHYSICAL START',flush=True);tick=time.perf_counter()
a=audit(graph,src/'output.route')
names={int(m[1]):m[2] for line in (src/'output.route').read_text().splitlines() if (m:=NET.match(line))}
valid=set(ep['net_names'].values())
observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in valid)
assert observed==required and a['overflow_units']==0
(O/'physical_audit.json').write_text(json.dumps(a)+'\n')
row['physical_audit_seconds']=time.perf_counter()-tick
print('PHYSICAL PASS; CANONICAL START',flush=True)
def limits():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def run(cmd,work,log,environment):
 with log.open('x') as stream:return subprocess.run(cmd,cwd=work,env=environment,stdout=stream,stderr=subprocess.STDOUT,preexec_fn=limits).returncode
canonical.run=run
inventory=Inventory(graph)
files={str(f):sha(f) for f in src.iterdir() if f.is_file()}
candidate={'files':files,'command':cmd,'width':128,'decision':'R','cpd_ns':row['diagnostic_cpd_ns']}
tick=time.perf_counter()
try:
 row['canonical']=canonical.canonical_reload(candidate,src,O/'canonical',inventory)
 assert row['canonical']['semantic_consistency_gate_pass']
 row['status']='FULL_PHYSICAL_AND_CANONICAL_PASS'
except Exception:
 row['status']='CANONICAL_AUDIT_FAILED';row['error']=traceback.format_exc()
row['canonical_audit_seconds']=time.perf_counter()-tick
assert all(sha(path)==h for path,h in p['bindings'].items())
row['bindings']={str(f):sha(f) for f in [Path(__file__),D/'protocol.json',src/'terminal.json',src/'native.log',src/'output.route',O/'physical_audit.json',Path(canonical.__file__)]}
row['scope']='Recovery audit of existing terminal artifacts; original native clocks preserved. Canonical analysis only newly executed. No native seed rerun, end-to-end or heldout claim.'
(O/'verification.json').write_text(json.dumps(row,indent=2)+'\n')
print(json.dumps({k:v for k,v in row.items() if k not in ['canonical','bindings','native_work']},indent=2),flush=True)
if row['status']!='FULL_PHYSICAL_AND_CANONICAL_PASS':raise SystemExit(1)
