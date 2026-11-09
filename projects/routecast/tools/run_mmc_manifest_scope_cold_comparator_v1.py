"""Fresh cold subprocess and all physical/canonical/ignored checks, matched to seed inputs."""
import sys,os,time,json,re,subprocess
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
from shared_compact_native_inventory_v1 import Inventory
from canonical_reload_pin_index_expat_v3 import canonical_reload
O=R/'experiments/mmc_manifest_scope_cold_comparator_v1_2026-10-10';O.mkdir();native=O/'native';native.mkdir();out=O/'postchecks';out.mkdir()
S=R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10';epfile=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json'
from shutil import copyfile
seedproof=json.loads((S/'verification.json').read_text());assert seedproof['complete_current_MMC_initial_floors_paths_epochs_prices_ledgers_events_and_seed_native_pass'] and all(sha(p)==v for p,v in seedproof['bindings'].items())
ss=json.loads((S/'native/service_receipt.json').read_text());bindings={str(Path(__file__).resolve()):sha(Path(__file__)),str(S/'verification.json'):sha(S/'verification.json'),str(epfile):sha(epfile)}
for p in [Path(ss['command'][0]),Path(ss['command'][1]),Path(ss['command'][ss['command'].index('--read_rr_graph')+1])]:bindings[str(p)]=sha(p)
for name in ['design.blif','design.net','design.place']:copyfile(S/'native'/name,native/name);assert sha(native/name)==sha(S/'native'/name);bindings[str(native/name)]=sha(native/name)
command=ss['command'].copy();env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};tick=time.perf_counter()
with (native/'native.log').open('w') as f:p=subprocess.run(command,cwd=native,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
native_seconds=time.perf_counter()-tick;assert p.returncode==0
s=dict(seed_imported=False,exit_code=p.returncode,command=command,files={str(p):sha(p) for p in native.iterdir() if p.is_file()},bindings=bindings,native_process_seconds=native_seconds,scope='Fresh cold native subprocess on exactly matched binary/arch/graph/net/place/options. No query service or seed. Timer covers native subprocess only, excluding audits and input acquisition.')
(native/'receipt.json').write_text(json.dumps(s,indent=2)+'\n');print('MATCHED COLD NATIVE PASS',native_seconds,flush=True)
ep=json.loads(epfile.read_text());assert len(ep['connections'])==115572
log=(native/'native.log').read_text();assert 'NET-aware seed imported' not in log and 'ROUTECAST_WIDTH' not in log and 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log
graph=Path(ep['inputs']['graph']['path']);route=native/'output.route';tick=time.perf_counter();physical=audit(graph,route);names={int(m[1]):m[2] for l in route.read_text().splitlines() if (m:=NET.match(l))};required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);netnames=set(ep['net_names'].values());observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in physical['connections'] if names[q['net_id']] in netnames);assert required==observed and physical['overflow_units']==0
(out/'physical_audit.json').write_text(json.dumps(physical)+'\n');physical_seconds=time.perf_counter()-tick;print('NATIVE_PHYSICAL_PASS',sum(required.values()),flush=True)
cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);candidate=dict(files=s['files'],command=s['command'],width=128,decision='R',cpd_ns=cpd)
canonical=O/'canonical';canonical.mkdir();tick=time.perf_counter();inv=Inventory(graph);result=canonical_reload(candidate,native,canonical/'mmc',inv);assert result['semantic_consistency_gate_pass'];canonical_seconds=time.perf_counter()-tick
(canonical/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=[dict(name='mmc',mode='cold',status='SEMANTIC_CANONICAL_PASS',canonical=result)]),indent=2)+'\n')
source=(R/'tools/verify_ultraembedded_mmc_seed_canonical_ignored_pins_v1.py').read_text();source=source.replace("R/'experiments/ultraembedded_mmc_seed_canonical_v1_2026-10-08'",f'Path({str(canonical)!r})').replace("R/'experiments/ultraembedded_mmc_native_demand_v1_2026-10-08'","R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand'").replace("R/'experiments/ultraembedded_mmc_rr_only_v1_2026-10-08'","R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr'")
adapter=out/'ignored_adapter.py';adapter.write_text(source)
with (out/'ignored_audit.log').open('w') as f:subprocess.run([sys.executable,str(adapter)],cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
for p in [epfile,graph,route,native/'native.log',out/'physical_audit.json',canonical/'receipt.json',adapter,out/'ignored_audit.log']:bindings[str(p)]=sha(p)
for p in canonical.glob('*verification*.json'):
 v=json.loads(p.read_text());assert all(sha(q)==v for q,v in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
assert all(sha(p)==v for p,v in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,all115572_native_physical_queries_and_full_XML_capacity_pass=True,native_FULL_and_canonical_semantic_pass=True,explicit_ignored_pin_audit_pass=True,native_process_seconds=native_seconds,physical_seconds=physical_seconds,canonical_seconds=canonical_seconds,diagnostic_cpd_ns=cpd,wirelength=wirelength,scope='Exposed MMC exact-input-matched fresh cold native candidate; independent native/canonical/ignored checks. No fresh cold arm/input-acquisition/fullworkflow netgain or strict functional heldout claim.'),indent=2)+'\n');print('ALL MMC POSTCHECKS PASS',flush=True)
