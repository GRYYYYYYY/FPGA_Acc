"""Finish local native audits from preserved successful output, no router rerun."""
import json,sys,os,re,time,resource,subprocess
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
from audit_mmc_v16_native_iteration_work_v1 import parse
from shared_compact_native_inventory_v1 import Inventory
import canonical_reload_pin_index_expat_v3 as canonical
D=R/'experiments/mmc_native_postprocess_recovery_v1_2026-10-18';O=D/'local_completed';O.mkdir(exist_ok=False);original=R/'experiments/mmc_native_seed_utility_pilot_v1_2026-10-18';source=original/'local';terminal=json.loads((source/'terminal.json').read_text());assert terminal['exit_status']==0 and not terminal['native_timeout'];pp=original/'protocol.json';protocol=json.loads(pp.read_text());assert all(sha(p)==h for p,h in protocol['bindings'].items());cmd=protocol['commands']['local'];epfile=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);seedproof=R/'experiments/mmc_native_local_seed_v1_2026-10-18/independent_verification_v1.json';v=json.loads(seedproof.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());log=(source/'native.log').read_text();assert 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log and 'NET-aware seed imported' in log
# Reuse successful native process observation; perform only independent postchecks.
row=dict(arm='local',exit_status=0,native_timeout=False,native_process_seconds=terminal['native_process_seconds'],iterations=int(re.search(r'Successfully routed after (\d+) routing iterations',log)[1]),wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]),diagnostic_cpd_ns=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]),native_work=parse(log),status='AUDIT_PENDING')
known=set(ep['net_names'].values());required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);tick=time.perf_counter();physical=audit(graph,source/'output.route');names={int(m[1]):m[2] for line in (source/'output.route').read_text().splitlines() if (m:=NET.match(line))};observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in physical['connections'] if names[q['net_id']] in known);assert observed==required and physical['overflow_units']==0
with (O/'physical_audit.json').open('x') as f:json.dump(physical,f);f.write('\n')
row['physical_postcheck_seconds']=time.perf_counter()-tick
files={str(p):sha(p) for p in source.iterdir() if p.is_file()};bindings={**v['bindings'],str(seedproof):sha(seedproof),str(pp):sha(pp),str(source/'terminal.json'):sha(source/'terminal.json'),str(D/'interruption.json'):sha(D/'interruption.json'),str(Path(__file__)):sha(__file__),**files}
def limits():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30))
def run(cmd,work,log,environment):
 with log.open('x') as f:return subprocess.run(cmd,cwd=work,env=environment,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limits).returncode
canonical.run=run;inventory=Inventory(graph);candidate=dict(files=files,command=cmd,width=128,decision='R',cpd_ns=row['diagnostic_cpd_ns']);tick=time.perf_counter();c=canonical.canonical_reload(candidate,source,O/'canonical',inventory);assert c['semantic_consistency_gate_pass'];row.update(canonical=c,canonical_audit_seconds=time.perf_counter()-tick,status='FULL_PHYSICAL_AND_CANONICAL_PASS');assert all(sha(p)==h for p,h in bindings.items())
for p in O.rglob('*'):
 if p.is_file():bindings[str(p)]=sha(p)
with (O/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,row=row,successful_native_output_reused_without_rerouting=True,indexed_membership_exact=True,scope='Recovered physical/canonical checks of original completed local native run. No new native process or full workflow timing; postcheck addresses quadratic constant-set construction only.'),f,indent=2);f.write('\n')
print('LOCAL RECOVERED FINAL GATES PASS',row['iterations'],row['wirelength'],row['diagnostic_cpd_ns'],flush=True)
