"""Single audit/evaluation continuation of the verified existing full forecast process."""
from pathlib import Path
import json,subprocess,sys,time,os,hashlib
R=Path(__file__).resolve().parents[1]
def save(p,d):
 temp=p.with_suffix('.tmp');temp.write_text(json.dumps(d,indent=2)+'\n');os.replace(temp,p)
def main():
 O=R/'experiments/mmc_complete_static_criticality_review_supervision_v1_2026-10-19';O.mkdir(exist_ok=False);M=R/'experiments/mmc_complete_static_criticality_forecast_v1_2026-10-19';owner=json.loads((M/'owner.json').read_text());own={'pid':os.getpid(),'startticks':Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19]};steps=['audit_MMC_complete_static_criticality_forecast_v1_2026_10_19.py','evaluate_MMC_complete_static_criticality_cold_quality_v1_2026_10_19.py'];bindings={str(R/'tools'/n):hashlib.sha256((R/'tools'/n).read_bytes()).hexdigest() for n in steps};save(O/'owner.json',dict(own,existing_model_owner=owner,steps=steps,bindings=bindings));rows=[]
 while not (M/'receipt.json').exists():
  stat=Path(f"/proc/{owner['pid']}/stat")
  if not stat.exists():
   if (M/'receipt.json').exists():break
   save(O/'terminal.json',{'status':'MODEL_OWNER_TERMINAL_WITHOUT_RECEIPT_NO_RESTART','steps':rows});return
  fields=stat.read_text().rsplit(')',1)[1].split()
  if fields[19]!=owner['startticks']:save(O/'terminal.json',{'status':'MODEL_PID_IDENTITY_CHANGED_NO_RESTART','steps':rows});return
  save(O/'progress.json',{'stage':'WAIT_EXISTING_MODEL','owner_verified':owner,'cpu_ticks':int(fields[11])+int(fields[12]),'utc_seconds':time.time()});time.sleep(15)
 if json.loads((M/'receipt.json').read_text())['status']!='ALL3_COMPLETE_STATIC_CRITICALITY_FORECASTS_PRODUCED_INDEPENDENT_XML_EVENT_AND_QUALITY_PENDING':save(O/'terminal.json',{'status':'MODEL_RECEIPT_NOT_ADMITTED','steps':rows});return
 for name in steps:
  path=R/'tools'/name
  if hashlib.sha256(path.read_bytes()).hexdigest()!=bindings[str(path)]:save(O/'terminal.json',{'status':'REVIEW_SCRIPT_SOURCE_DRIFT_STOPPED','step':name});return
  print('COMPLETE_REVIEW_START',name,flush=True)
  with (O/(name+'.log')).open('x') as log:
   child=subprocess.Popen([sys.executable,str(path)],cwd=R,stdout=log,stderr=subprocess.STDOUT);save(O/'live_step.json',{'script':name,'pid':child.pid,'startticks':Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19]});code=child.wait()
  rows.append({'script':name,'returncode':code});save(O/'progress.json',{'steps':rows});print('COMPLETE_REVIEW_DONE',name,code,flush=True)
  if code:save(O/'terminal.json',{'status':'REVIEW_FAILURE_PRESERVED_STOPPED','steps':rows});return
 save(O/'terminal.json',{'status':'ALL3_SELECTED_STATE_AUDIT_AND_FROZEN_COLD_EVALUATION_COMPLETE_NUMERICAL_GATE_SEPARATE','steps':rows,'scope':'No independent metric verifier yet, no full original gate due missing raw_min_on, no native policy or full research completion claim.'})
if __name__=='__main__':main()
