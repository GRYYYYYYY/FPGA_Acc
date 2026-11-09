"""Execute fixed matched six native runs after real zero-state admission."""
import pathlib,json,hashlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def main():
 P=R/'experiments/mmc_native_excess_utility_protocol_v1_2026-10-19/protocol.json';spec=json.loads(P.read_text());O=R/'experiments/mmc_native_excess_utility_v1_2026-10-19';runner=R/'tools/run_MMC_native_excess_utility_case_v1_2026_10_19.py';I=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19';zp=R/'experiments/mmc_preload_zero_state_equivalence_v2_2026-10-19/zero_state_contract_v1.json';z=json.loads(zp.read_text());assert z['status']=='SNAPSHOT_ENABLED_ZERO_NATIVE_EQUIVALENCE_AND_ALL904438_INITIAL_COST_BITS_PASS';assert z['readback']['all_nodes_checked']==904438 and z['readback']['changed_initial_costs']==0
 proof=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/independent_prediction_verification_v1.json';a=json.loads(proof.read_text());assert a['status']=='ALL3_COMPLETE_NET_ENSEMBLE_IDENTITY_XML_DAG_EXPECTATION_AND_LEDGER_AUDIT_PASS';bindings={**spec['bindings'],str(P):sha(P),str(zp):sha(zp),str(proof):sha(proof),str(runner):sha(runner),str(pathlib.Path(__file__).resolve()):sha(__file__),str(R/'tools/preload_state_readback_contract_v1.py'):sha(R/'tools/preload_state_readback_contract_v1.py')}
 for evidence in [z,a]:
  for p,h in evidence['bindings'].items():assert sha(p)==h,p
 for p,h in bindings.items():assert sha(p)==h,p
 assert [(x['case'],x['arm']) for x in spec['jobs']]==[(f'episode_{i:02d}',arm) for i in range(1,4) for arm in ['zero','forecast']]
 for job in spec['jobs']:
  argv=job['argv'];assert argv[argv.index('--num_workers')+1]=='1' and argv[argv.index('--route_chan_width')+1]=='128' and argv[argv.index('--seed')+1]=='1';graph=pathlib.Path(argv[argv.index('--read_rr_graph')+1]);assert sha(graph)==job['environment_set']['ROUTECAST_EXCESS_GRAPH_SHA256'];risk=pathlib.Path(job['environment_set']['ROUTECAST_EXCESS_PRELOAD']);assert bindings[str(risk)]==sha(risk)
  source=pathlib.Path(job['input_directory']);baseline=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/job['case']/'cold'
  for name in ['design.blif','design.net','design.place']:assert sha(source/name)==sha(baseline/name);bindings[str(source/name)]=sha(source/name)
 if '--check-only' in sys.argv:print('READY fixed6 native jobs; all bindings and zero-state proof admitted');return
 O.mkdir();write(O/'input_admission.json',dict(bindings=bindings,all_inputs_and_zero_equivalence_admitted=True,scope='Admitted fixed initial-cost experiment only. Original cold occupancy quality failed, no unseen-family or end-to-end gain claim.'));rows=[]
 for job in spec['jobs']:
  case,arm=job['case'],job['arm'];parent=O/case;parent.mkdir(exist_ok=True);out=parent/arm
  print('NATIVE UTILITY START',case,arm,flush=True)
  with (parent/(arm+'.log')).open('x') as f:code=subprocess.run([sys.executable,str(runner),str(I/case),str(out),arm],cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
  row=dict(case=case,arm=arm,exit_code=code);rows.append(row);write(parent/(arm+'_execution.json'),row);print('NATIVE UTILITY TERMINAL',row,flush=True)
  if code:write(O/'terminal.json',dict(status='NATIVE_OR_READBACK_OR_AUDIT_FAILED',rows=rows,policy_not_retuned=True));raise SystemExit(code)
 write(O/'terminal.json',dict(status='ALL6_NATIVE_READBACK_PHYSICAL_CANONICAL_PASS',rows=rows,independent_full_trace_and_utility_gate_pending=True,complete_workflow_gain_proven=False))
if __name__=='__main__':main()
