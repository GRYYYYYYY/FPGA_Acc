"""One read-only wait owner; verify successful handoff, then complete native checks."""
import sys,os,time,json,re,subprocess
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
from shared_compact_native_inventory_v1 import Inventory
from canonical_reload_pin_index_expat_v3 import canonical_reload
O=R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10';native=O/'native';handoff=O/'handoff';out=O/'postchecks';out.mkdir();pid=int(sys.argv[1]);token=sys.argv[2];epfile=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json'
def state():
 try:
  s=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();return s[0],s[19]
 except FileNotFoundError:return None
current=state();assert current is not None and current[1]==token and current[0]!='Z','original driver must be live at queue submission'
(out/'waiting.json').write_text(json.dumps(dict(owner_pid=os.getpid(),wait_for_pid=pid,wait_for_starttime=token,scope='Exactly one native postcheck owner. Wait only; no retry/resubmission/recovery.'),indent=2)+'\n');print('POSTCHECK_QUEUE_WAITING',os.getpid(),pid,flush=True)
while True:
 s=state()
 if s is None or s[0]=='Z' or s[1]!=token:break
 time.sleep(5)
assert (handoff/'receipt.json').exists(),'driver ended without successful handoff receipt; no automatic recovery'
h=json.loads((handoff/'receipt.json').read_text());bindings={str(Path(__file__).resolve()):sha(Path(__file__)),str(handoff/'receipt.json'):sha(handoff/'receipt.json')}
for section in ['bindings','files']:assert all(sha(p)==v for p,v in h[section].items());bindings.update(h[section])
s=json.loads((native/'service_receipt.json').read_text());assert s['seed_imported'] and s['exit_code']==0
for section in ['bindings','files']:assert all(sha(p)==v for p,v in s[section].items());bindings.update(s[section])
ep=json.loads(epfile.read_text());assert h['required_connections']==len(ep['connections'])==115572 and h['selected_connections']+h['pending_connections']==115572
log=(native/'native.log').read_text();assert 'NET-aware seed imported' in log and 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log
graph=Path(ep['inputs']['graph']['path']);route=native/'output.route';tick=time.perf_counter();physical=audit(graph,route);names={int(m[1]):m[2] for l in route.read_text().splitlines() if (m:=NET.match(l))};required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);netnames=set(ep['net_names'].values());observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in physical['connections'] if names[q['net_id']] in netnames);assert required==observed and physical['overflow_units']==0
(out/'physical_audit.json').write_text(json.dumps(physical)+'\n');physical_seconds=time.perf_counter()-tick;print('NATIVE_PHYSICAL_PASS',sum(required.values()),flush=True)
cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);candidate=dict(files=s['files'],command=s['command'],width=128,decision='R',cpd_ns=cpd)
canonical=O/'canonical';canonical.mkdir();tick=time.perf_counter();inv=Inventory(graph);result=canonical_reload(candidate,native,canonical/'mmc',inv);assert result['semantic_consistency_gate_pass'];canonical_seconds=time.perf_counter()-tick
(canonical/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=[dict(name='mmc',mode='seed',status='SEMANTIC_CANONICAL_PASS',canonical=result)]),indent=2)+'\n')
source=(R/'tools/verify_ultraembedded_mmc_seed_canonical_ignored_pins_v1.py').read_text();source=source.replace("R/'experiments/ultraembedded_mmc_seed_canonical_v1_2026-10-08'",f'Path({str(canonical)!r})').replace("R/'experiments/ultraembedded_mmc_native_demand_v1_2026-10-08'","R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand'").replace("R/'experiments/ultraembedded_mmc_rr_only_v1_2026-10-08'","R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr'")
adapter=out/'ignored_adapter.py';adapter.write_text(source)
with (out/'ignored_audit.log').open('w') as f:subprocess.run([sys.executable,str(adapter)],cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
for p in [epfile,graph,route,native/'native.log',out/'physical_audit.json',canonical/'receipt.json',adapter,out/'ignored_audit.log']:bindings[str(p)]=sha(p)
for p in canonical.glob('*verification*.json'):
 v=json.loads(p.read_text());assert all(sha(q)==v for q,v in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
assert all(sha(p)==v for p,v in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,all115572_native_physical_queries_and_full_XML_capacity_pass=True,native_FULL_and_canonical_semantic_pass=True,explicit_ignored_pin_audit_pass=True,physical_seconds=physical_seconds,canonical_seconds=canonical_seconds,diagnostic_cpd_ns=cpd,wirelength=wirelength,scope='Exposed MMC current fixed RR/placement complete seed candidate; independent native/canonical/ignored checks. No fresh cold arm/input-acquisition/fullworkflow netgain or strict functional heldout claim.'),indent=2)+'\n');print('ALL MMC POSTCHECKS PASS',flush=True)
