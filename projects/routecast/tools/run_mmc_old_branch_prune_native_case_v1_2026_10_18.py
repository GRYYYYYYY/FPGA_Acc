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
case=sys.argv[1];assert case in ['case_01','case_02','case_03'];prep=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case;proof=prep/'staged_input_verification_v1.json';v=json.loads(proof.read_text());assert v['all_native_logical_NET_local_pin_identities_preserved'] and not v['native_route_labels_generated']
bindings={**v['bindings'],str(proof):sha(proof),**closure([Path(__file__)])}
B=R/'build/native_partial_net_lookahead_v1_2026-10-18';b=json.loads((B/'receipt.json').read_text());binary=B/'sequence_vpr';assert sha(binary)==b['binary_sha256']
bindings.update(b['bindings']);bindings[str(B/'receipt.json')]=sha(B/'receipt.json');bindings[str(binary)]=sha(binary)
for p in [reload_binary,identity]:bindings[str(p)]=sha(p)
epfile=prep/'demand/endpoints.json';ep=json.loads(epfile.read_text());src=prep/'mmc';graph=Path(ep['inputs']['graph']['path']);arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
bindings[str(arch)]=sha(arch)
frozen_protocol=R/'experiments/mmc_multiplacement_geometry_v1_2026-10-18/cohort_protocol.json';bindings[str(frozen_protocol)]=sha(frozen_protocol);seedroot=R/'experiments/mmc_old_branch_prune_seeds_v1_2026-10-18';seedproof=seedroot/'seed_admission_verification_v1.json';sv=json.loads(seedproof.read_text());assert sv['all3_partialNET_old_branch_seeds_independently_admitted'];bindings.update(sv['bindings']);bindings[str(seedproof)]=sha(seedproof);seeds={'old_branch_prune':str(seedroot/case/'seed.route')};eqproof=R/'experiments/mmc_partial_seed_engine_equivalence_v1_2026-10-18/equivalence_verification_v1.json';eq=json.loads(eqproof.read_text());assert eq['no_seed_and_complete_NET_seed_old_behavior_equal'];bindings.update(eq['bindings']);bindings[str(eqproof)]=sha(eqproof)

assert all(sha(p)==h for p,h in bindings.items())
O=R/'experiments/mmc_old_branch_prune_native_v1_2026-10-18'/case;O.mkdir()
commands={}
for arm in (['old_branch_prune'] if case=='case_01' else ['cold','old_branch_prune']):
 d=O/arm;d.mkdir()
 for name in ['design.blif','design.net','design.place']:shutil.copyfile(src/name,d/name);bindings[str(src/name)]=sha(src/name)
 commands[arm]=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
(O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,commands=commands,order=list(commands),child_address_space_limit_bytes=CHILD_LIMIT,child_timeout_seconds=CHILD_TIMEOUT,canonical_run_wrapper='Original canonical body unchanged; subprocess wrapper adds same32GiB child limit; no elapsed-time cancellation.',native_seed_paths=seeds,scope='Supplemental old-branch-pruned partialNET control. New engine old-behavior equivalence and all3seed admission required. Case01 uses already validated same-build cold reference; cases02/03 get same-build cold observations. Complete115572native queries mandatory; cached exposed-control study, no fresh full-flow benefit or retroactive15arm screen change.'),indent=2)+'\n')
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
