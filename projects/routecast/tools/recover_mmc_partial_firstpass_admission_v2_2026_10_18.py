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
B=R/'build/native_partial_net_firstpass_v1_2026-10-18';b=json.loads((B/'receipt.json').read_text());binary=B/'sequence_vpr';assert sha(binary)==b['binary_sha256']
bindings.update(b['bindings']);bindings[str(B/'receipt.json')]=sha(B/'receipt.json');bindings[str(binary)]=sha(binary)
for p in [reload_binary,identity]:bindings[str(p)]=sha(p)
epfile=prep/'demand/endpoints.json';ep=json.loads(epfile.read_text());src=prep/'mmc';graph=Path(ep['inputs']['graph']['path']);arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
bindings[str(arch)]=sha(arch)
frozen_protocol=R/'experiments/mmc_multiplacement_geometry_v1_2026-10-18/cohort_protocol.json';bindings[str(frozen_protocol)]=sha(frozen_protocol);seedroot=R/'experiments/mmc_old_branch_prune_seeds_v1_2026-10-18';seedproof=seedroot/'seed_admission_verification_v1.json';sv=json.loads(seedproof.read_text());assert sv['all3_partialNET_old_branch_seeds_independently_admitted'];bindings.update(sv['bindings']);bindings[str(seedproof)]=sha(seedproof);seeds={arm:str(seedroot/case/'seed.route') for arm in ['off','on']}
for mode in ['off','on']:
 eqproof=R/('experiments/mmc_partial_firstpass_equivalence_'+mode+'_v1_2026-10-18/equivalence_verification_v1.json');eq=json.loads(eqproof.read_text());assert eq['no_seed_and_complete_NET_seed_old_behavior_equal'];bindings.update(eq['bindings']);bindings[str(eqproof)]=sha(eqproof)


assert all(sha(p)==h for p,h in bindings.items())
original=R/'experiments/mmc_partial_firstpass_native_v1_2026-10-18'/case;original_protocol=json.loads((original/'protocol.json').read_text());bindings[str(original/'protocol.json')]=sha(original/'protocol.json');seed_receipt=seedroot/case/'receipt.json';sr=json.loads(seed_receipt.read_text());bindings[str(seed_receipt)]=sha(seed_receipt);selected=set(sr['selected_connection_ids']);counts={}
for q in ep['connections']:
 count=counts.setdefault(q['net_id'],[0,0]);count[0 if q['connection_id'] in selected else 1]+=1
partial=[x for x in counts.values() if x[0] and x[1]];expected=(len(partial),sum(x[0] for x in partial),sum(x[1] for x in partial));assert expected[0]==sr['retained_partial_NETs']
O=R/'experiments/mmc_partial_firstpass_recovery_v2_2026-10-18'/case;O.mkdir()
commands={}
for arm in ['off','on']:
 d=O/arm;d.mkdir()
 for name in ['design.blif','design.net','design.net.post_routing','design.place','native.log','output.route']:
  source=original/arm/name;assert source.is_file();(d/name).symlink_to(source);bindings[str(source)]=sha(source)
 commands[arm]=original_protocol['commands'][arm]

(O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,commands=commands,order=list(commands),child_address_space_limit_bytes=CHILD_LIMIT,child_timeout_seconds=CHILD_TIMEOUT,canonical_run_wrapper='Original canonical body unchanged; subprocess wrapper adds same32GiB child limit; no elapsed-time cancellation.',native_seed_paths=seeds,scope='Postprocessing recovery only: original native processes not rerun. Correct expected eligible-partial pending count from admitted selected CID partition; preserve original failed harness and all native outputs. FULL physical canonical admission unchanged.'),indent=2)+'\n')
required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);inventory=Inventory(graph);rows=[]
for arm,cmd in commands.items():
 d=O/arm;env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 env['ROUTECAST_NATIVE_SEED']=seeds[arm]
 if arm=='on':env['ROUTECAST_PRESERVE_PARTIAL_FIRST_ITERATION']='1'
 if arm=='off':
  priorproof=original/'verification.json';prior=json.loads(priorproof.read_text());assert all(sha(p)==h for p,h in prior['bindings'].items());bindings.update(prior['bindings']);bindings[str(priorproof)]=sha(priorproof)
  row=dict(next(r for r in prior['rows'] if r['arm']=='off'));assert row['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';row['native_rerun']=False;row['reused_admitted_off_audit']=True
  (d/'physical_audit.json').symlink_to(original/arm/'physical_audit.json');rows.append(row);print('REUSE ADMITTED OFF',case,flush=True);continue
 terminal=original/arm/'terminal.json';saved=json.loads(terminal.read_text());bindings[str(terminal)]=sha(terminal);code=saved['exit_status'];assert code==0 and saved['native_timeout'] is False
 row=dict(arm=arm,exit_status=code,native_timeout=False,native_process_seconds=saved['native_process_seconds'],native_rerun=False,original_terminal=str(terminal),status='NATIVE_OR_AUDIT_FAILED')
 print('RECOVERY AUDIT ONLY',case,arm,flush=True)
 try:
  assert code==0
  log=(d/'native.log').read_text();assert 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log
  assert 'NET-aware seed imported' in log
  if arm=='on':
   match=re.search(r'first-pass partial eligibility nets=(\d+) present=(\d+) pending=(\d+)',log);assert match
   assert tuple(map(int,match.groups()))==expected
   row['firstpass_eligibility']={'nets':int(match[1]),'present':int(match[2]),'pending':int(match[3])}
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
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,native_reruns=0,expected_partial_eligibility=dict(nets=expected[0],present=expected[1],pending=expected[2]),all_native_physical_and_canonical_pass=all(r['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' for r in rows),scope='Native endpoint/arc/capacity/FULL and canonical ignored-pin consistency. CPD diagnostic on experimental architecture; no end-to-end net gain or heldout claim.'),indent=2)+'\n')
if not all(r['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' for r in rows):raise SystemExit(1)
