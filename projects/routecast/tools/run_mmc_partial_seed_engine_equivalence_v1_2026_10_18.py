"""MMC trim envelope repair only; original failed cohort preserved."""
import json,sys,os,time,subprocess,shutil,re,resource
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
from audit_mmc_v16_native_iteration_work_v1 import parse as parse_iteration_work
from shared_compact_native_inventory_v1 import Inventory
from canonical_reload_pin_index_expat_v3 import canonical_reload,binary as reload_binary,identity
R=Path(__file__).resolve().parents[1]
# Limit only this comparison's child processes; never signal external jobs.
CHILD_LIMIT=32*2**30
CHILD_TIMEOUT=None
import canonical_reload_pin_index_expat_v3 as canonical_module
def child_limits():resource.setrlimit(resource.RLIMIT_AS,(CHILD_LIMIT,CHILD_LIMIT))
def canonical_run(cmd,work,log,environment):
 with log.open('x') as stream:
  return subprocess.run(cmd,cwd=work,env=environment,stdout=stream,stderr=subprocess.STDOUT,timeout=CHILD_TIMEOUT,preexec_fn=child_limits).returncode
canonical_module.run=canonical_run
prep=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_01';proof=prep/'staged_input_verification_v1.json';v=json.loads(proof.read_text());assert v['all_native_logical_NET_local_pin_identities_preserved'] and not v['native_route_labels_generated']
bindings={**v['bindings'],str(proof):sha(proof),**closure([Path(__file__)])}
B=R/'build/native_partial_net_lookahead_v1_2026-10-18';b=json.loads((B/'receipt.json').read_text());binary=B/'sequence_vpr';assert sha(binary)==b['binary_sha256']
bindings.update(b['bindings']);bindings[str(B/'receipt.json')]=sha(B/'receipt.json');bindings[str(binary)]=sha(binary)
for p in [reload_binary,identity]:bindings[str(p)]=sha(p)
epfile=prep/'demand/endpoints.json';ep=json.loads(epfile.read_text());src=prep/'mmc';graph=Path(ep['inputs']['graph']['path']);arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
bindings[str(arch)]=sha(arch)
frozen_protocol=R/'experiments/mmc_multiplacement_geometry_v1_2026-10-18/cohort_protocol.json';bindings[str(frozen_protocol)]=sha(frozen_protocol);seeds={'retained_off':str(R/'experiments/mmc_v2_native_seed_inputs_v1_2026-10-18/case_01/retained_off/seed.route')};seedproof=R/'experiments/mmc_v2_native_seed_inputs_v1_2026-10-18/seed_admission_verification_v1.json';sv=json.loads(seedproof.read_text());assert sv['all12_seeds_independently_admitted'];bindings.update(sv['bindings']);bindings[str(seedproof)]=sha(seedproof)
assert all(sha(p)==h for p,h in bindings.items())
O=R/'experiments/mmc_partial_seed_engine_equivalence_v1_2026-10-18';O.mkdir()
commands={}
for arm in ['cold','retained_off']:
 d=O/arm;d.mkdir()
 for name in ['design.blif','design.net','design.place']:shutil.copyfile(src/name,d/name);bindings[str(src/name)]=sha(src/name)
 commands[arm]=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
(O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,commands=commands,order=list(commands),child_address_space_limit_bytes=CHILD_LIMIT,child_timeout_seconds=CHILD_TIMEOUT,canonical_run_wrapper='Original canonical body unchanged; subprocess wrapper adds same32GiB child limit; no elapsed-time cancellation.',native_seed_paths=seeds,scope='New isolated partial-seed lookahead build on existingcase01 cold and complete-NET V2retained_off seeds. Require exact route bytes/counters/wire/diagnostic CPD versus archived original-binary outputs after full admission. No partial-NET test or speed claim yet.'),indent=2)+'\n')
required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);inventory=Inventory(graph);rows=[]
for arm,cmd in commands.items():
 d=O/arm;env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 if arm!='cold':env['ROUTECAST_NATIVE_SEED']=seeds[arm]
 free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());assert free>=CHILD_LIMIT+8*2**30
 tick=time.perf_counter();print('NATIVE START',arm,flush=True)
 timed_out=False
 with (d/'native.log').open('x') as log:
  try:code=subprocess.run(cmd,cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=CHILD_TIMEOUT,preexec_fn=child_limits).returncode
  except subprocess.TimeoutExpired:code=None;timed_out=True
 row=dict(arm=arm,exit_status=code,native_timeout=timed_out,native_process_seconds=time.perf_counter()-tick,status='NATIVE_OR_AUDIT_FAILED')
 (d/'terminal.json').write_text(json.dumps(row)+'\n')
 try:
  assert code==0
  log=(d/'native.log').read_text();assert 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log
  if arm!='cold':assert 'NET-aware seed imported' in log
  row['wirelength']=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);row['diagnostic_cpd_ns']=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);row['iterations']=int(re.search(r'Successfully routed after (\d+) routing iterations',log)[1])
  row['native_work']=parse_iteration_work(log);assert row['native_work']['iterations']==row['iterations']
  a=audit(graph,d/'output.route');names={int(m[1]):m[2] for line in (d/'output.route').read_text().splitlines() if (m:=NET.match(line))}
  known_names=set(ep['net_names'].values());observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in known_names);assert observed==required and a['overflow_units']==0
  (d/'physical_audit.json').write_text(json.dumps(a)+'\n')
  files={str(p):sha(p) for p in d.iterdir() if p.is_file()};candidate=dict(files=files,command=cmd,width=128,decision='R',cpd_ns=row['diagnostic_cpd_ns']);tick=time.perf_counter()
  result=canonical_reload(candidate,d,O/(arm+'_canonical'),inventory);assert result['semantic_consistency_gate_pass'];row['canonical_audit_seconds']=time.perf_counter()-tick;row['canonical']=result;row['status']='FULL_PHYSICAL_AND_CANONICAL_PASS'
 except Exception as exc:row['error']=repr(exc)
 rows.append(row);(O/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(arm,row['status'],row.get('error',''),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
for p in O.rglob('*'):
 if p.is_file():bindings[str(p)]=sha(p)
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_native_physical_and_canonical_pass=all(r['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' for r in rows),scope='Native endpoint/arc/capacity/FULL and canonical ignored-pin consistency. CPD diagnostic on experimental architecture; no end-to-end net gain or heldout claim.'),indent=2)+'\n')
if not all(r['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' for r in rows):raise SystemExit(1)

reference=R/'experiments/mmc_v2_native_utility_v1_2026-10-18/case_01';rp=reference/'verification.json';old=json.loads(rp.read_text());assert old['all_native_physical_and_canonical_pass'] and all(sha(p)==h for p,h in old['bindings'].items());eqbindings={**bindings,**old['bindings'],str(rp):sha(rp),str(O/'verification.json'):sha(O/'verification.json')};checks=[]
for row in rows:
 arm=row['arm'];prior=next(x for x in old['rows'] if x['arm']==arm);assert sha(O/arm/'output.route')==sha(reference/arm/'output.route') and row['wirelength']==prior['wirelength'] and row['diagnostic_cpd_ns']==prior['diagnostic_cpd_ns'];assert 'Initializing router criticalities' in (O/arm/'native.log').read_text()
 for key in ['iterations','total_heap_pushes','total_rerouted_NET_operations','total_rerouted_connection_operations']:assert row['native_work'][key]==prior['native_work'][key]
 for a,b in zip(row['native_work']['rows'],prior['native_work']['rows']):
  for key in ['iteration','BB_updates','heap_pushes','rerouted_NET_operations','rerouted_connection_operations','overused_RR_nodes']:assert a[key]==b[key]
 checks.append(dict(arm=arm,route_bytes_equal=True,full_native_and_canonical_semantic_pass=True,all_integer_work_and_wire_and_printed_diagnostic_CPD_equal=True))
assert all(sha(p)==h for p,h in eqbindings.items())
with (O/'equivalence_verification_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=eqbindings,checks=checks,no_seed_and_complete_NET_seed_old_behavior_equal=True,partial_NET_import_completion_still_pending=True,scope='Two actual native/FULL/physical/canonical runs match original bytes and integer counters. No timing equivalence/gain or partial-seed completion claimed.'),f,indent=2)
print('PARTIAL ENGINE OLD-BEHAVIOR EQUIVALENCE PASS',flush=True)
