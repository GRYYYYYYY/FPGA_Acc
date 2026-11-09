"""Bounded read-only initial-record parity; not final model admission."""
import resource,json,hashlib,time
from pathlib import Path
from audit_raw_floor_initial_parity_v1_2026_10_17 import audit
R=Path(__file__).resolve().parents[1];D=R/'experiments/neuron_raw_floor_initial_record_precheck_v1_2026-10-18';D.mkdir(exist_ok=False)
A=R/'experiments/neuron_raw_floor_trial_v1_2026-10-17/model';B=R/'experiments/neuron_proxy_budget_trial_v2_2026-10-17/model'
limit=512*2**20;free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());assert free>=limit+8*2**30
resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
files=[Path(__file__).resolve(),R/'tools/audit_raw_floor_initial_parity_v1_2026_10_17.py',A/'initial.json',B/'initial.json',A/'floors.json',B/'floors.json']
bindings={str(p):sha(p) for p in files}
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,address_space_limit_bytes=limit,shared_headroom_before_bytes=free,scope='Only closed initial-output files read while feedback model continues. No writes/signals to current model; complete independent audits remain pending.'),f,indent=2);f.write('\n')
start=time.perf_counter();a=json.loads((A/'initial.json').read_text());b=json.loads((B/'initial.json').read_text());parity=audit(a,b)
assert parity['connections']==77106 and parity['changed_equal_cost_initial_paths']==1667
assert sha(A/'floors.json')==sha(B/'floors.json') and all(sha(k)==h for k,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,all_pass=True,initial_record_parity=parity,floors_byte_identical=True,seconds=time.perf_counter()-start,process_sampled_HWM_scope='rusage maxRSS for this bounded precheck process, not the model or complete final admission.',precheck_maxrss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,scope='All77106initial records numeric/nonpath parity only. Changed initial paths/ledgers allowed and not physically admitted by this check. Full model, all3audits and all8metrics still required; no gain claim.'),f,indent=2);f.write('\n')
print(json.dumps(dict(parity=parity,maxrss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2))
