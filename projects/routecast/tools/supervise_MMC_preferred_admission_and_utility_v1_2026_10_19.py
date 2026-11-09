"""Single continuation owner: existing parity -> independent review -> faults -> fixed3 utility."""
import json,subprocess,sys,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def save(p,d):
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2)+'\n');os.replace(tmp,p)
def main():
 O=R/'experiments/mmc_preferred_pipeline_supervision_v1_2026-10-19';O.mkdir(exist_ok=False)
 parity=R/'experiments/mmc_preferred_hint_runtime_parity_v1_2026-10-19';checkpoint=json.loads((R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json').read_text())['mmc_NET_conditioned_hint_contract_v1'];pid=checkpoint['runtime_parity_supervisor_pid'];ticks=checkpoint['runtime_parity_supervisor_startticks'];steps=[]
 save(O/'owner.json',{'pid':os.getpid(),'startticks':Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19],'original_parity_pid':pid,'original_parity_startticks':ticks,'policy':'No restart, retry or new policy choice. Stop on any failed evidence.'})
 while not (parity/'terminal.json').exists():
  stat=Path(f'/proc/{pid}/stat')
  if not stat.exists() or stat.read_text().rsplit(')',1)[1].split()[19]!=ticks:
   if (parity/'terminal.json').exists():break
   save(O/'terminal.json',{'status':'ORIGINAL_PARITY_SUPERVISOR_MISSING_WITHOUT_TERMINAL_NO_RESTART'});return
  save(O/'progress.json',{'stage':'WAIT_EXISTING_PARITY','observed_utc_seconds':time.time(),'original_pid_verified':pid});time.sleep(10)
 assert json.loads((parity/'terminal.json').read_text())['status']=='ALL9_DISABLED_AND_EMPTY_HINT_RUNTIME_PARITY_PASS'
 for name in ['verify_MMC_preferred_runtime_parity_v1_2026_10_19.py','run_MMC_preferred_native_import_faults_v1_2026_10_19.py','run_MMC_preferred_NET_native_utility_cohort_v1_2026_10_19.py']:
  print('PIPELINE_START',name,flush=True)
  with (O/(name+'.log')).open('x') as log:
   child=subprocess.Popen([sys.executable,str(R/'tools'/name)],cwd=R,stdout=log,stderr=subprocess.STDOUT);save(O/'live_step.json',{'step':name,'pid':child.pid,'startticks':Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19]});code=child.wait()
  steps.append({'step':name,'returncode':code});save(O/'progress.json',{'steps':steps});print('PIPELINE_DONE',name,code,flush=True)
  if code:save(O/'terminal.json',{'status':'ADMISSION_OR_UTILITY_FAILURE_PRESERVED_STOPPED','steps':steps});return
 save(O/'terminal.json',{'status':'ADMISSION_AND_ALL3_NATIVE_UTILITY_TERMINAL_INDEPENDENT_WORK_REPLAY_PENDING','steps':steps,'scope':'No primary utility success or full research completion claimed.'})
if __name__=='__main__':main()
