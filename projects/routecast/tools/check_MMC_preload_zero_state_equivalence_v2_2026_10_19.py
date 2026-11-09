"""Cold observer equivalence on an archived exposed MMC layout, never new targets."""
import json,pathlib,hashlib,subprocess,shutil,os,resource,re
from audit_mmc_v16_native_iteration_work_v1 import parse
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def limits():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 B=R/'build/native_excess_preload_state_v2_2026-10-19';bp=B/'receipt.json';b=json.loads(bp.read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and b['hook_removal_recovers_original_source_exactly']
 baseline=R/'experiments/mmc_multiplacement_cold_labels_v1_2026-10-18/case_01';proof=baseline/'verification.json';v=json.loads(proof.read_text());assert v['all_native_physical_and_canonical_pass'];ref=v['rows'][0];assert ref['arm']=='cold'
 for p,h in b['bindings'].items():assert sha(p)==h,p
 for p,h in v['bindings'].items():assert sha(p)==h,p
 O=R/'experiments/mmc_preload_zero_state_equivalence_v2_2026-10-19';O.mkdir();out=O/'cold';out.mkdir()
 cmd=json.loads((baseline/'protocol.json').read_text())['commands']['cold'];cmd[0]=str(B/'sequence_vpr');bindings={str(bp):sha(bp),str(proof):sha(proof),str(B/'sequence_vpr'):sha(B/'sequence_vpr'),str(pathlib.Path(__file__).resolve()):sha(__file__)}
 for name in ['design.net','design.place','design.blif']:
  p=baseline/'cold'/name;shutil.copyfile(p,out/name);bindings[str(p)]=sha(p)
 env={k:x for k,x in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_NATIVE_OWNER_TRACE']=str(out/'owner_trace.tsv')
 zero=R/'experiments/mmc_ensemble_excess_preload_v1_2026-10-19/zero.risk';zproof=zero.parent/'verification.json';z=json.loads(zproof.read_text());assert z['bindings'][str(zero)]==sha(zero);graph=pathlib.Path(cmd[cmd.index('--read_rr_graph')+1]);assert z['bindings'][str(graph)]==sha(graph);bindings[str(zero)]=sha(zero);bindings[str(zproof)]=sha(zproof);env['ROUTECAST_EXCESS_PRELOAD']=str(zero);env['ROUTECAST_EXCESS_GRAPH_SHA256']=sha(graph);env['ROUTECAST_EXCESS_STATE_DUMP']=str(out/'preload_state.bin')
 write(O/'protocol.json',dict(bindings=bindings,command=cmd,environment_clear_prefix='ROUTECAST_',environment_set={'ROUTECAST_NATIVE_OWNER_TRACE':str(out/'owner_trace.tsv')},scope='Archived exposed case01 preload zero equivalence only; no nonzero policy runs or utility claim.'))
 print('COLD OBSERVER EQUIVALENCE START',flush=True)
 with (out/'native.log').open('x') as f:code=subprocess.run(cmd,cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limits).returncode
 result=dict(status='FAILED',native_exit_code=code)
 try:
  assert code==0;log=(out/'native.log').read_text();assert 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log;assert 'initial excess preload entries=0 changed=0' in log
  actual=parse(log);expected=ref['native_work']
  for k in ['iterations','total_heap_pushes','total_rerouted_NET_operations','total_rerouted_connection_operations']:assert actual[k]==expected[k],k
  for x,y in zip(actual['rows'],expected['rows']):
   for k in ['iteration','BB_updates','heap_pushes','rerouted_NET_operations','rerouted_connection_operations','overused_RR_nodes']:assert x[k]==y[k],k
  stats=lambda s:re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',s)
  assert len(stats(log))==1 and stats(log)==stats((baseline/'cold/native.log').read_text())
  for name in ['output.route','design.net.post_routing']:assert sha(out/name)==sha(baseline/'cold'/name),name
  trace=out/'owner_trace.tsv'
  with trace.open('rb') as f:
   assert f.readline()==b'TRACE 1\n';f.seek(max(0,trace.stat().st_size-256));assert f.read().splitlines()[-1].startswith(b'END 1 ')
  result.update(status='ARCHIVED_COLD_BYTES_AND_INTEGER_WORK_EQUAL',native_work=actual,full_physical_canonical_admission_transferred_by_exact_input_output_bytes=True,independent_trace_replay_pending=True)
 except Exception as exc:result['error']=repr(exc)
 for p in out.iterdir():
  if p.is_file():bindings[str(p)]=sha(p)
 write(O/'receipt.json',dict(bindings=bindings,**result));print(result['status'],result.get('error',''),flush=True)
 if result['status']=='FAILED':raise SystemExit(1)
if __name__=='__main__':main()
