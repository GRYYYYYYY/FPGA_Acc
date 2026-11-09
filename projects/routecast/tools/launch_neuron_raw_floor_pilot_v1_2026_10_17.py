"""Single-owner bounded large pilot, no recovery/retry or external signals."""
import json,hashlib,resource,subprocess,sys,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/neuron_raw_floor_pilot_launch_v1_2026-10-17';D.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(n,d):
 with (D/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
gate=R/'experiments/xtea_raw_floor_abba_v3_2026-10-17/verification.json';v=json.loads(gate.read_text());assert v['both_orders_astar_component_faster'] and v['all_four_complete_floors_paths_fraction_RC_and_singleparents_pass']
for section in ['bindings','outputs']:
 for p,h in v[section].items():assert sha(p)==h
assert sha(gate.parent/'rows.json')==v['rows_sha256']
driver=R/'tools/pilot_neuron_quotient_raw_floors_v1_2026_10_17.py';output=R/'experiments/neuron_quotient_raw_floor_pilot_v1_2026-10-17';assert not output.exists()
bindings={str(p):sha(p) for p in [Path(__file__).resolve(),driver,gate]}
limit=20*2**30;margin=8*2**30;available=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());assert available>=limit+margin
command=[sys.executable,'-u',str(driver)]
write('protocol.json',dict(bindings=bindings,command=command,output=str(output),child_address_space_limit_bytes=limit,shared_available_before_bytes=available,margin_bytes=margin,no_elapsed_scientific_timeout=True,retry=False,scope='All77106initialfloor connections, actual frozen node-base tables, original physical/Fraction audit. No feedback/native route run, no complete-model acceleration or quality claim. Original baseline graph/floors are read-only.'))
start=time.perf_counter()
def limits():resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
with (D/'pilot.log').open('x') as log:
 child=subprocess.Popen(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
 write('process.json',dict(pid=child.pid,args=command,start_stat=Path(f'/proc/{child.pid}/stat').read_text(),child_address_space_limit_bytes=limit))
 print('NEURON RAW FLOOR PILOT START',child.pid,flush=True);code=child.wait()
write('terminal.json',dict(exit_status=code,seconds=time.perf_counter()-start,child_address_space_limit_bytes=limit))
assert all(sha(k)==h for k,h in bindings.items())
if code:raise SystemExit(code)
p=output/'verification.json';pval=json.loads(p.read_text());assert pval['all77106_exact_archived_floors_original_XML_Fraction_RC_and_singleparents_pass']
write('verification.json',dict(bindings={**bindings,str(p):sha(p),str(D/'terminal.json'):sha(D/'terminal.json')},large_pilot_complete=True,scope='Full initial-floor pilot and independent audit only; no paired large-design timing, full feedback, QoR, heldout or end-to-end benefit.'))
print('NEURON RAW FLOOR PILOT PASS',flush=True)
