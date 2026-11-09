"""Fixed disabled6 and enabled-empty3 native parity controls; no policy utility runs."""
import pathlib,json,hashlib,shutil,subprocess,resource,os,time,re
from audit_mmc_v16_native_iteration_work_v1 import parse
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 P=R/'experiments/mmc_first_hint_connection_work_protocol_v1_2026-10-19/protocol.json';p=json.loads(P.read_text());B=R/'build/native_preferred_NET_hint_v1_2026-10-19';bp=B/'receipt.json';b=json.loads(bp.read_text());assert b['status']=='PRIVATE_NATIVE_PREFERRED_HINT_BUILD_PASS_RUNTIME_PENDING' and sha(B/'sequence_vpr')==b['binary_sha256'];F=R/'experiments/mmc_first_iteration_hint_utility_protocol_v1_2026-10-19/protocol.json';f=json.loads(F.read_text());O=R/'experiments/mmc_preferred_hint_runtime_parity_v1_2026-10-19';O.mkdir(exist_ok=False);bindings={str(x):sha(x) for x in [P,bp,F,B/'sequence_vpr',pathlib.Path(__file__).resolve(),R/'tools/audit_mmc_v16_native_iteration_work_v1.py']};plans=[]
 for doc in [p]:
  for path,h in doc['bindings'].items():assert sha(pathlib.Path(path))==h
 graph=f['jobs'][0]['environment_set']['ROUTECAST_EXCESS_GRAPH_SHA256']
 zero=O/'zero.rcpref2';zero.write_text(f'RCPREF2 {graph} 904438 55304 1 0 0\n');bindings[str(zero)]=sha(zero)
 jobs=[dict(j,mode='disabled') for j in p['jobs']]+[dict(j,mode='enabled_empty') for j in p['jobs'] if j['arm']=='zero']
 for job in jobs:
  case,arm=job['case'],job['arm'];ref=pathlib.Path(job['reference_directory']);proof=pathlib.Path(job['reference_proof']);v=json.loads(proof.read_text());assert v['all_native_physical_and_canonical_pass'];spec=next(j for j in f['jobs'] if j['case']==case and j['arm']==arm);d=O/job['mode']/case/arm;argv=spec['argv'].copy();argv[0]=str(B/'sequence_vpr');env={k:(str(d/pathlib.Path(value).name) if str(ref) in value else value) for k,value in spec['environment_set'].items()};env['ROUTECAST_NATIVE_CONNECTION_TRACE']=str(d/'connection_trace.tsv');env.update({'ROUTECAST_PREFERRED_NET_CLAIMS':str(zero)} if job['mode']=='enabled_empty' else {});plans.append(dict(mode=job['mode'],case=case,arm=arm,reference=str(ref),reference_proof=str(proof),cwd=str(d),argv=argv,environment_set=env));bindings[str(proof)]=sha(proof)
  for name in ['design.blif','design.net','design.place','output.route','design.net.post_routing','owner_trace.tsv','native.log','preload_state.bin','expiry_before.bin','expiry_after.bin']:
   path=ref/name;assert v['bindings'][str(path)]==sha(path);bindings[str(path)]=sha(path)
 write(O/'execution_protocol.json',dict(jobs=plans,bindings=bindings,child_address_space_limit_bytes=32*2**30,order='fixed disabled6 then enabled-empty3',failure_policy='Stop on observation/equivalence failure, preserve it and accept no affected labels; no outcome repair or retry.',scope='Read-only measurement replay of current frozen policies, no policy,scale,TTL,seed or target change. Native clocks not a performance experiment.'))
 rows=[]
 for plan in plans:
  case,arm=plan['case'],plan['arm'];D=pathlib.Path(plan['cwd']);D.mkdir(parents=True);ref=pathlib.Path(plan['reference']);v=json.loads(pathlib.Path(plan['reference_proof']).read_text());prior=v['rows'][0]
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(ref/name,D/name);assert sha(D/name)==bindings[str(ref/name)]
  assert int(pathlib.Path('/sys/fs/cgroup/memory.max').read_text())-int(pathlib.Path('/sys/fs/cgroup/memory.current').read_text())>=40*2**30
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(plan['environment_set']);print('FIRST_HINT_CONNECTION_OBSERVE_START',case,arm,flush=True);t=time.perf_counter()
  def limits():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  with (D/'native.log').open('x') as log:
   child=subprocess.Popen(plan['argv'],cwd=D,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits);write(O/'live_process.json',dict(case=case,arm=arm,pid=child.pid,startticks=pathlib.Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19]));code=child.wait()
  row=dict(mode=plan['mode'],case=case,arm=arm,native_exit_code=code,native_seconds_diagnostic_only=time.perf_counter()-t,status='NATIVE_OR_OBSERVER_EQUIVALENCE_FAILED');error=None
  try:
   assert code==0;text=(D/'native.log').read_text();
   scopes=re.findall(r'ROUTECAST preferred NET query scopes=(\d+)',text);assert (len(scopes)==1 and int(scopes[0])>0) if plan['mode']=='enabled_empty' else not scopes;assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
   for name in ['output.route','design.net.post_routing','owner_trace.tsv','preload_state.bin','expiry_before.bin','expiry_after.bin']:assert sha(D/name)==bindings[str(ref/name)],name
   actual=parse(text);old=parse((ref/'native.log').read_text());fields=['iteration','present_factor_text','BB_updates','heap_pushes','rerouted_NET_operations','rerouted_connection_operations','overused_RR_nodes'];assert [{k:x[k] for k in fields} for x in actual['rows']]==[{k:x[k] for k in fields} for x in old['rows']]
   stats=lambda txt:re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',txt);assert len(stats(text))==1 and stats(text)==stats((ref/'native.log').read_text());wire=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]);cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1]);assert wire==prior['wirelength'] and cpd==prior['diagnostic_cpd_ns'];trace=D/'connection_trace.tsv'
   with trace.open('rb') as stream:
    assert stream.readline()==b'CONNECTION_TRACE 2\n';stream.seek(max(0,trace.stat().st_size-512));end=stream.read().splitlines()[-1].split();assert len(end)==7 and end[:2]==[b'END',b'1'];attempts,successes,failures,pushes,pops=map(int,end[2:]);assert attempts==successes+failures and successes==actual['total_rerouted_connection_operations'];native_pushes,native_pops=map(int,stats(text)[0][2:]);assert pushes<=native_pushes and pops<=native_pops
   row.update(status='EXACT_CURRENT_REFERENCE_BYTES_WORK_AND_EXPIRY_PASS',successful_sink_operations=successes,failed_sink_attempts=failures,attributed_heap_pushes=pushes,attributed_heap_pops=pops,outside_sink_heap_pushes=native_pushes-pushes,outside_sink_heap_pops=native_pops-pops,physical_canonical_reference_admission_transferred_by_exact_input_output_bytes=True,original_zero_counter_gate_pass=prior['canonical']['original_zero_counter_gate_pass'],wirelength=wire,CPD_ns=cpd,independent_CID_replay_pending=True,preferred_scope_count=int(scopes[0]) if scopes else 0)
  except Exception as e:row['error']=repr(e);error=e
  files={str(x):sha(x) for x in D.iterdir() if x.is_file()};write(D/'equivalence.json',dict(row=row,bindings=files,reference_proof=plan['reference_proof']));rows.append(row);write(O/'progress.json',dict(rows=rows));print('FIRST_HINT_CONNECTION_OBSERVE_DONE',case,arm,row['status'],row.get('error',''),flush=True)
  if error:write(O/'terminal.json',dict(status='OBSERVER_OR_EQUIVALENCE_FAILED_STOPPED_WITHOUT_RETRY',rows=rows));raise RuntimeError('Observation not admitted; original policy/outcomes unchanged') from error
 write(O/'terminal.json',dict(status='ALL9_DISABLED_AND_EMPTY_HINT_RUNTIME_PARITY_PASS',rows=rows,independent_explicit_sink_replay_and_CID_binding_pending=True,scope='Measurements only, no new policy acceptance or performance claim.'))
if __name__=='__main__':main()
