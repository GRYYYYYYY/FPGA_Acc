"""Fixed12 arms in isolated processes, own3 gate first, at most3 concurrent jobs."""
import json,sys,copy,subprocess,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from verify_external_initial_response_observer_source_v1 import trees
E=R/'experiments';D=E/'prospective_external_family_full_rr_pressure_factorial_v1_2026-10-19';B=R/'build/native_external_full_rr_pressure_intervention_v1_2026-10-19';I=E/'prospective_external_family_early_net_observer_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 protocol=read(D/'protocol.json');build=read(B/'receipt.json');contract=read(E/'full_rr_pressure_guard_contract_v1_2026-10-19/verification.json');inputs=read(D/'independent_input_verification_v1.json')
 for d in [protocol,build,contract,inputs]:assert all(sha(p)==h for p,h in d['bindings'].items())
 assert sha(build['binary'])==build['binary_sha256'];base=read(I/'target_manifest.json');cases=[]
 for arm in ['channel_0_nonchannel_0','channel_1_nonchannel_0','channel_0_nonchannel_1','channel_1_nonchannel_1']:
  for c in protocol['cases']:
   a=next(a for a in c['arms'] if a['arm']==arm);r=copy.deepcopy(c['original_manifest_case']);r['case']=c['case']+'/'+arm;r['command'][0]=build['binary'];r['inputs']['pressure']=a['pressure'];r['output']=a['native_output'];cases.append(r)
 base['cases']=cases;base['bindings'].update(protocol['bindings']);base['bindings'].update(build['bindings']);base['bindings'].update({str(D/'protocol.json'):sha(D/'protocol.json'),build['binary']:build['binary_sha256'],str(Path(__file__).resolve()):sha(__file__),str(R/'tools/run_external_pressure_native_case_v1.py'):sha(R/'tools/run_external_pressure_native_case_v1.py')});mp=D/'manifest.json'
 with mp.open('x') as f:json.dump(base,f,indent=2)
 def run(c):
  folder=Path(c['output']);log=folder.parent/'execution.log'
  with log.open('x') as f:code=subprocess.run([sys.executable,str(R/'tools/run_external_pressure_native_case_v1.py'),str(mp),c['case']],cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
  proof=folder/'verification.json';a=read(proof) if proof.exists() else {};case,arm=c['case'].rsplit('/',1);same=None
  if (folder/'output.route').exists():same=trees(folder/'output.route')==trees(I/case/'output.route')
  row=dict(case=case,arm=arm,process_exit=code,status=a.get('status','MISSING_NATIVE_VERIFICATION'),error=a.get('error'),final_tree_identical_to_original=same)
  if arm=='channel_0_nonchannel_0':row['own_control_pass']=code==0 and a.get('status')=='FULL_PHYSICAL_AND_CANONICAL_PASS' and same is True and sha(folder/'early_net_trace.tsv')==sha(I/case/'early_net_trace.tsv') and sha(folder/'iteration_support.tsv')==sha(I/case/'iteration_support.tsv')
  with (folder.parent/'execution_receipt.json').open('x') as f:json.dump(row,f,indent=2)
  print(json.dumps(row),flush=True);return row
 results=[]
 for phase in range(4):
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:batch=list(pool.map(run,cases[3*phase:3*phase+3]))
  results.extend(batch)
  if phase==0 and not all(r['own_control_pass'] for r in batch):
   with (D/'terminal.json').open('x') as f:json.dump(dict(status='OWN_CONTROLS_FAILED_INTERVENTIONS_NOT_RUN',rows=results),f,indent=2)
   return
 with (D/'terminal.json').open('x') as f:json.dump(dict(status='ALL12_FROZEN_FULL_RR_PRESSURE_FACTORIAL_ARMS_TERMINAL',rows=results,scope='All12 retained including failed native outcomes. At most3 isolated processes, no same-process monkeypatch concurrency. Diagnostic only.'),f,indent=2)
if __name__=='__main__':main()
