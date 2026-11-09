"""Fixed3 preferred NET utility cohort; no automatic policy tuning/retries."""
import json,sys,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 protocol=R/'experiments/mmc_preferred_NET_native_utility_protocol_v1_2026-10-19/protocol.json';spec=json.loads(protocol.read_text());parity=R/'experiments/mmc_preferred_hint_runtime_parity_v1_2026-10-19/independent_verification_v1.json';faults=R/'experiments/mmc_preferred_native_import_faults_v1_2026-10-19/terminal.json'
 assert json.loads(parity.read_text())['status']=='ALL9_FULL_ARTIFACT_CONNECTION_TRACE_NATIVE_WORK_AND_EMPTY_SCOPE_COVERAGE_PASS'
 assert json.loads(faults.read_text())['status']=='ALL4_NATIVE_IMPORT_FAULTS_REJECTED_BEFORE_PRELOAD_OUTPUT'
 for p,h in spec['bindings'].items():assert sha(p)==h
 assert [j['case'] for j in spec['jobs']]==['episode_01','episode_02','episode_03']
 runner=R/'tools/run_MMC_preferred_NET_native_utility_case_v1_2026_10_19.py';O=R/'experiments/mmc_preferred_NET_native_utility_v1_2026-10-19';O.mkdir(exist_ok=False)
 save(O/'input_admission.json',{'status':'FIXED3_NATIVE_UTILITY_ADMITTED_NOT_OUTCOME_ACCEPTED','bindings':{str(p):sha(p) for p in [protocol,parity,faults,runner,Path(__file__).resolve()]}});rows=[]
 for job in spec['jobs']:
  case=job['case'];prep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}';cmd=[sys.executable,str(runner),str(prep),job['cwd'],'preferred'];print('PREFERRED_NATIVE_UTILITY_START',case,flush=True)
  with (O/f'{case}.log').open('x') as log:
   child=subprocess.Popen(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT);save(O/'live_case_process.json',{'case':case,'pid':child.pid,'startticks':Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19]});code=child.wait()
  row={'case':case,'returncode':code};rows.append(row);save(O/'progress.json',{'rows':rows});print('PREFERRED_NATIVE_UTILITY_DONE',case,code,flush=True)
  if code!=0:save(O/'terminal.json',{'status':'SEMANTIC_OR_INTEGRITY_FAILURE_PRESERVED_STOPPED','rows':rows});raise RuntimeError('Preferred native utility not admitted')
 save(O/'terminal.json',{'status':'ALL3_NATIVE_FULL_PHYSICAL_CANONICAL_AND_EXPIRY_PASS_WORK_REPLAY_PENDING','rows':rows,'scope':'All numerical utility outcomes retained; no promotion or gain claim before independent replay and frozen gate.'})
if __name__=='__main__':main()
