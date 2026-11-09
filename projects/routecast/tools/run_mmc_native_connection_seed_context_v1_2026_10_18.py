"""Six new observation runs, matched immutable baselines; no routing policy tuning."""
import json,sys,os,re,subprocess,shutil,resource,struct
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from parse_native_work_exact_totals_v2_2026_10_18 import parse
spec=R/'experiments/mmc_native_owner_cascade_trace_spec_v1_2026-10-18.json';P=json.loads(spec.read_text());assert len(P['jobs'])==6
B=R/'build/native_connection_seed_context_v1_2026-10-18';bp=B/'receipt.json';b=json.loads(bp.read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and b['status']=='connection_seed_context_observer_build_pass_runtime_pending'
wp=R/'experiments/mmc_partial_firstpass_recovery_v3_2026-10-18/independent_wire_work_comparison_v1.json';w=json.loads(wp.read_text());assert w['all6_independent_wire_and_every_iteration_integer_fields_equal']
bindings={**P['bindings'],**b['bindings'],**w['bindings'],**closure([Path(__file__)]),str(spec):sha(spec),str(bp):sha(bp),str(wp):sha(wp),str(B/'sequence_vpr'):sha(B/'sequence_vpr')}
legacy=R/'experiments/mmc_native_connection_work_cascade_trace_v1_2026-10-18';legacyp=legacy/'cohort_equivalence.json';legacyproof=json.loads(legacyp.read_text());assert legacyproof['all6_native_full_output_bytes_integer_counters_equal'];bindings[str(legacyp)]=sha(legacyp)
cache=Cache()
with cache.installed():
 assert all(sha(p)==h for p,h in bindings.items())
 refs={}
 for case in ['case_01','case_02','case_03']:
  p=(R/'experiments/mmc_partial_firstpass_recovery_v3_2026-10-18'/case/'verification.json').resolve();v=json.loads(p.read_text());assert v['all_native_physical_and_canonical_pass'] and all(sha(p)==h for p,h in v['bindings'].items());refs[case]=v;bindings.update(v['bindings']);bindings[str(p)]=sha(p)
D=R/'experiments/mmc_native_connection_seed_context_v1_2026-10-18';D.mkdir();(D/'logs').mkdir()
commands={}
for job in P['jobs']:
 case=job['case'];arm='on' if job['preserve_partial_first_iteration'] else 'off';original=Path(job['baseline_route']).parent
 oldprotocol=R/'experiments/mmc_partial_firstpass_native_v1_2026-10-18'/case/'protocol.json';assert bindings[str(oldprotocol)]==sha(oldprotocol)
 cmd=json.loads(oldprotocol.read_text())['commands'][arm].copy();cmd[0]=str(B/'sequence_vpr')
 assert cmd[cmd.index('--num_workers')+1]=='1' and cmd[cmd.index('--route_chan_width')+1]=='128' and cmd[cmd.index('--seed')+1]=='1' and cmd[cmd.index('--check_route')+1]=='full'
 if not (D/case).exists():(D/case).mkdir()
 out=D/case/arm;out.mkdir()
 for name in ['design.net','design.place','design.blif']:shutil.copyfile(original/name,out/name);assert sha(original/name)==sha(out/name);bindings[str(out/name)]=sha(out/name)
 for path in [Path(job['seed']),original/'output.route',original/'design.net.post_routing',original/'native.log']:assert bindings[str(path)]==sha(path)
 commands[(case,arm)]=cmd
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,jobs=P['jobs'],commands={c+':'+a:x for (c,a),x in commands.items()},max_concurrent_cases=1,order_within_case=['off','on'],child_address_space_limit_bytes=32*2**30,child_timeout_seconds=None,scope='Fresh actual route-tree heap seed insertion observation, serial stop-on-first-failure; not a rerun to repair old outcomes. Same policy,seed,graph,inputs; route and packed-net bytes, all integer counters and printed diagnostic CPD equality mandatory. Full old physical/canonical admission transferred only by exact byte/input equality. Independent trace replay remains a separate gate; no timing gain.'),f,indent=2)
def limits():
 resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def run_case(case):
 rows=[]
 for job in [j for j in P['jobs'] if j['case']==case]:
  arm='on' if job['preserve_partial_first_iteration'] else 'off';out=D/case/arm;old=Path(job['baseline_route']).parent;cmd=commands[(case,arm)];trace=out/'owner_trace.tsv'
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_NATIVE_SEED']=job['seed'];env['ROUTECAST_NATIVE_OWNER_TRACE']=str(trace);env['ROUTECAST_NATIVE_CONNECTION_TRACE']=str(out/'connection_trace.tsv');env['ROUTECAST_NATIVE_SEED_CONTEXT_TRACE']=str(out/'seed_context.bin')
  if arm=='on':env['ROUTECAST_PRESERVE_PARTIAL_FIRST_ITERATION']='1'
  print('NATIVE SEED CONTEXT OBSERVATION START',case,arm,flush=True)
  with (out/'native.log').open('x') as f:code=subprocess.run(cmd,cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limits,timeout=None).returncode
  row=dict(case=case,arm=arm,native_exit_code=code,status='NATIVE_OR_EQUIVALENCE_FAILED')
  with (out/'terminal.json').open('x') as f:json.dump(row,f)
  try:
   assert code==0
   text=(out/'native.log').read_text();assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
   prior=next(r for r in refs[case]['rows'] if r['arm']==arm);actual=parse(text)
   for key in ['iterations','total_heap_pushes','total_rerouted_NET_operations','total_rerouted_connection_operations']:assert actual[key]==prior['native_work'][key],key
   for x,y in zip(actual['rows'],prior['native_work']['rows']):
    for key in ['iteration','BB_updates','heap_pushes','rerouted_NET_operations','rerouted_connection_operations','overused_RR_nodes']:assert x[key]==y[key],key
   stats=lambda s:re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',s)
   assert len(stats(text))==1 and stats(text)==stats((old/'native.log').read_text())
   wire=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]);cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1]);assert wire==prior['wirelength'] and cpd==prior['diagnostic_cpd_ns']
   for name in ['output.route','design.net.post_routing','design.net','design.place','design.blif']:assert sha(out/name)==sha(old/name),name
   assert trace.stat().st_size>0
   with trace.open('rb') as f:
    assert f.readline()==b'TRACE 1\n';f.seek(max(0,trace.stat().st_size-256));assert f.read().splitlines()[-1].startswith(b'END 1 ')
   connection=out/'connection_trace.tsv';assert connection.stat().st_size>0
   with connection.open('rb') as stream:
    assert stream.readline()==b'CONNECTION_TRACE 2\n';stream.seek(max(0,connection.stat().st_size-512));end=stream.read().splitlines()[-1].split();assert len(end)==7 and end[:2]==[b'END',b'1'];attempts,successful,failed=map(int,end[2:5]);attributed_pushes,attributed_pops=map(int,end[5:7]);assert attempts==successful+failed
   assert successful==actual['total_rerouted_connection_operations']
   native_pushes,native_pops=map(int,stats(text)[-1][2:]);assert attributed_pushes<=native_pushes and attributed_pops<=native_pops
   for name in ['connection_trace.tsv','owner_trace.tsv']:
    previous=legacy/case/arm/name;assert sha(previous)==legacyproof['bindings'][str(previous)] and sha(out/name)==sha(previous)
   seeds=out/'seed_context.bin'
   with seeds.open('rb') as f:
    header=f.readline();assert header==b'RC_SEED_PUSH_LE64 1\n';f.seek(-32,2);footer=struct.unpack('<QQQQ',f.read(32));assert footer[0]==2**64-1 and footer[1]==footer[2]+footer[3] and seeds.stat().st_size==len(header)+32*(footer[1]+1);assert footer[2]<=attributed_pushes
   row['route_tree_seed_push_records']=footer[1];row['seed_pushes_inside_attempts']=footer[2];row['seed_pushes_outside_attempts']=footer[3];row['legacy_owner_and_connection_traces_byte_equal']=True
   row['attributed_sink_heap_pushes']=attributed_pushes;row['attributed_sink_heap_pops']=attributed_pops;row['outside_sink_heap_pushes']=native_pushes-attributed_pushes;row['outside_sink_heap_pops']=native_pops-attributed_pops
   row['connection_attempts']=attempts;row['successful_native_sink_operations']=successful;row['failed_sink_attempts']=failed;row['distinct_manifest_CID_RRR_certified']=False
   row.update(status='MATCHED_NATIVE_FULL_BYTES_AND_INTEGER_COUNTERS_PASS',wirelength=wire,diagnostic_cpd_ns=cpd,native_work=actual,trace_bytes=trace.stat().st_size,baseline_route_sha256=sha(old/'output.route'),baseline_packed_net_sha256=sha(old/'design.net.post_routing'),full_physical_and_canonical_admission_transferred_by_exact_input_and_output_byte_equality=True,canonical_original_zero_counter_gate_pass=prior['canonical']['original_zero_counter_gate_pass'],canonical_fixups=prior['canonical']['fixups'],independent_trace_replay_pending=True)
  except Exception as e:row['error']=repr(e)
  rows.append(row)
  file_bindings={str(p):sha(p) for p in out.iterdir() if p.is_file()}
  with (out/'equivalence.json').open('x') as f:json.dump(dict(bindings=file_bindings,row=row),f,indent=2)
  print('NATIVE SEED CONTEXT OBSERVATION TERMINAL',case,arm,row['status'],row.get('error',''),flush=True)
  if row['status']!='MATCHED_NATIVE_FULL_BYTES_AND_INTEGER_COUNTERS_PASS':raise RuntimeError('Stop on first observer/equivalence failure; preserve exact original artifacts')
 return rows
rows=[]
for case in ['case_01','case_02','case_03']:
 rows.extend(run_case(case));(D/'stages.json').write_text(json.dumps(rows,indent=2))
assert len(rows)==6 and all(r['status']=='MATCHED_NATIVE_FULL_BYTES_AND_INTEGER_COUNTERS_PASS' for r in rows)
with cache.installed():assert all(sha(p)==h for p,h in bindings.items())
for case in ['case_01','case_02','case_03']:
 for arm in ['off','on']:
  p=D/case/arm/'equivalence.json';v=json.loads(p.read_text());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
with (D/'cohort_equivalence.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all6_native_full_output_bytes_integer_counters_equal=True,all6_physical_canonical_admission_transferred_by_exact_bytes=True,independent_trace_replay_pending=True,scope='Observational native replay with identical outputs and integer work. Counter-zero gate unchanged; trace causal interpretation still unproven and clocks not comparable.'),f,indent=2)
print('ALL6NATIVE OWNER OBSERVATIONS MATCH ARCHIVED BASELINES',flush=True)
