"""Follow existing matrix PID; never restart or infer its exit status."""
import json,time,subprocess,sys
from pathlib import Path
out=Path('experiments/frisc_pressure_completion_chain_2026-10-05');pid=3587580;root=Path('experiments/frisc_pressure_candidate_matrix_2026-10-05')
if out.exists():raise ValueError('sole fresh chain required')
out.mkdir();(out/'source.py').write_text(Path(__file__).read_text())
proc=Path(f'/proc/{pid}/cmdline')
assert proc.exists() and b'frisc_pressure_candidate_matrix.py' in proc.read_bytes()
(out/'state.json').write_text(json.dumps({'state':'waiting_existing_process','pid':pid,'original_session':29029,'original_exit_code':None})+'\n')
while proc.exists():
 try:command=proc.read_bytes()
 except FileNotFoundError:break
 if b'frisc_pressure_candidate_matrix.py' not in command:break
 time.sleep(2)
receipt=json.loads((root/'receipt.json').read_text());assert len(receipt['reports'])==18
results=[]
for name in ('audit_frisc_pressure_matrix.py','evaluate_frisc_pressure_matrix.py'):
 with (out/(name+'.log')).open('w') as log:result=subprocess.run([sys.executable,str(Path('tools')/name)],stdout=log,stderr=subprocess.STDOUT)
 results.append({'script':name,'exit_code':result.returncode})
 if result.returncode:
  (out/'state.json').write_text(json.dumps({'state':'audit_or_evaluation_failed','original_exit_code':None,'results':results})+'\n');raise SystemExit(result.returncode)
(out/'state.json').write_text(json.dumps({'state':'audit_and_evaluation_complete','original_exit_code':None,'original_status_scope':'process identity gone and complete receipt present; primary must obtain original session terminal exit code','results':results},indent=2)+'\n');print(json.dumps(results),flush=True)
