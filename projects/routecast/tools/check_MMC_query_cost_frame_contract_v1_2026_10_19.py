"""Guard/RAII fault tests and cloned actual904438-node cost snapshots; no native routing."""
import pathlib,json,hashlib,subprocess,resource
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 C=R/'experiments/mmc_preferred_NET_claims_v1_2026-10-19';rp=C/'receipt.json';vp=C/'independent_verification_v1.json';r=json.loads(rp.read_text());v=json.loads(vp.read_text());assert v['status']=='ALL3_SOFT_PREFERRED_NET_CLAIMS_EXACT_AND_GEOMETRY_VERIFIED';D=R/'build/net_conditioned_query_cost_frame_v1_2026-10-19';binary=D/'check_query_cost_frame';header=R/'tools/net_conditioned_hint_contract_v1/query_cost_frame.h';source=R/'tools/net_conditioned_hint_contract_v1/check_query_cost_frame.cpp';O=R/'experiments/net_conditioned_query_cost_frame_contract_v1_2026-10-19';O.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [rp,vp,binary,header,source,pathlib.Path(__file__).resolve()]};results=[]
 def limits():resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 def run(tag,args,code,marker):
  result=subprocess.run([str(binary),*map(str,args)],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,preexec_fn=limits);(O/(tag+'.log')).write_text(result.stdout);assert result.returncode==code and marker in result.stdout,(tag,result.returncode,result.stdout);row=dict(test=tag,exit_code=result.returncode,expected_exit_code=code,output=result.stdout.strip());results.append(row);print('QUERY_COST_FRAME_TEST',tag,result.returncode,result.stdout.strip(),flush=True)
 run('randomized_and_deterministic',[],0,'SYNTHETIC_PASS ')
 run('unexpected_history_preservation',['--unexpected-history'],86,'UNEXPECTED_HISTORY_PRESERVED_FAIL_CLOSED')
 run('unclosed_frame_fail_closed',['--leak-frame'],87,'ACTIVE_FRAME_LEAK_ARMED')
 run('scoped_history_violation_fail_closed',['--raii-history'],87,'SCOPED_UNEXPECTED_HISTORY_ARMED')
 for case in r['cases']:
  name=case['case'];input_file=pathlib.Path(case['cost_frame_input']);reference=R/'experiments/mmc_first_iteration_hint_utility_v1_2026-10-19'/name/'forecast';proof=reference/'verification.json';p=json.loads(proof.read_text());initial=reference/'cold/preload_state.bin';after=reference/'cold/expiry_after.bin';physical=reference/'cold/physical_audit.json';assert p['all_native_physical_and_canonical_pass'];assert json.loads(physical.read_text())['inputs_sha256']['graph']==r['graph_sha256']
  for f in [initial,after]:assert p['bindings'][str(f)]==sha(f)
  assert v['bindings'][str(input_file)]==sha(input_file);run(name+'_cloned_actual_cost_arrays',['--snapshot',initial,after,input_file],0,'REAL_SNAPSHOT_PASS 904438 55304 ')
  for f in [input_file,proof,initial,after,physical]:bindings[str(f)]=sha(f)
 for f,h in bindings.items():assert sha(pathlib.Path(f))==h
 for f in O.glob('*.log'):bindings[str(f)]=sha(f)
 result=dict(status='QUERY_COST_FRAME_RANDOM_FAULT_RAII_AND_ALL3_CLONED_ACTUAL_SNAPSHOT_CONTRACTS_PASS',tests=results,bindings=bindings,synthetic_states=2000,cost_store_single_borrow_and_foreign_stale_nested_tokens_checked=True,all3_actual_graph_cost_words=904438,preferred_claim_files_independently_admitted=True,new_native_policy_jobs_launched=0,native_query_integration_proven=False,native_utility_proven=False,scope='Standalone C++ cost-array prototype only. Random full-array scope/restore, no-op modes, cold/serial guards, exception cleanup, unexpected-history atomic rejection and fail-closed exits tested. Three real native initial/expired snapshots cloned into separate test process arrays; original files and live native state never written. Native accessor/NET binding integration and runtime equivalence remain separate prerequisites; no actual ownership, history or route performance claim.')
 (O/'verification.json').open('x').write(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
