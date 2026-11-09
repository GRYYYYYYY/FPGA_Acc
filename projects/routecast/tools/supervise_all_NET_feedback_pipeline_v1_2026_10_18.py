"""Observe one fixed producer; run admitted audits and quality once, never restart."""
import json,os,subprocess,sys,time,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';out=E/'mmc_all_NET_feedback_v1_2026-10-18'
pid=int(sys.argv[1]);expected=sys.argv[2]
def identity():
 try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:return None
assert identity()==expected
receipt=out/'pipeline_supervision.json';assert not receipt.exists()
def record(status,**kw):
 data=dict(status=status,producer_pid=pid,producer_startticks=expected,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw);tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2));os.replace(tmp,receipt)
record('waiting_for_original_producer')
while not (out/'results.json').exists():
 if identity()!=expected:
  record('producer_terminal_without_results_no_restart');raise SystemExit(1)
 time.sleep(5)
assert json.loads((out/'results.json').read_text())['status']=='all3_global_schedule_feedback_complete_independent_audits_pending'
for phase,script in [('auditing','audit_mmc_all_NET_feedback_v1_2026_10_18.py'),('quality','run_mmc_all_NET_feedback_quality_v1_2026_10_18.py')]:
 record(phase);print('PIPELINE',phase,flush=True)
 with (out/f'pipeline_{phase}.log').open('x') as log:code=subprocess.call([sys.executable,str(R/'tools'/script)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 if code:record('failed',phase=phase,exit_code=code);raise SystemExit(code)
record('candidate_audits_and_original_quality_evaluation_complete');print('PIPELINE COMPLETE',flush=True)
