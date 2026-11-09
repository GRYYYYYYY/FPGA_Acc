"""Single-owner deterministic queue; observe original producer, never restart."""
import json,os,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path('experiments/alu4_free_pin_cohort_2026-10-05');out=root/'postprocess_queue';out.mkdir();owner=os.open(out/'owner.lock',os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(owner,str(os.getpid()).encode());os.close(owner)
identity=json.loads((root/'producer_identity.json').read_text());pid=identity['pid'];commands=[['python3','tools/audit_alu4_free_pin_cohort_queries.py'],['python3','tools/audit_alu4_free_pin_cohort_state.py'],['python3','tools/alu4_export_free_pin_cohort_route.py'],['python3','tools/alu4_free_pin_cohort_native_analysis.py'],['python3','tools/alu4_free_pin_cohort_native_comparison.py']];bindings={cmd[1]:sha(cmd[1]) for cmd in commands};bindings['tools/supervise_alu4_free_pin_postprocess.py']=sha(__file__)
plan={'producer':identity,'commands':commands,'command_source_sha256':bindings,'cwd':str(Path.cwd()),'policy':'wait only for original PID/starttime; no recovery/restart; verify complete receipt/identities then run bound stages once, stop at first failure','source_sha256':sha(__file__)};(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');reports=[];start=time.monotonic()
def save(status,**extra):
 r={'status':status,'supervisor_pid':os.getpid(),'producer':identity,'stage_reports':reports,'plan_sha256':sha(out/'plan.json'),'elapsed_s':time.monotonic()-start,**extra};temp=out/'status.tmp';temp.write_text(json.dumps(r,indent=2)+'\n');temp.replace(out/'status.json')
try:
 while True:
  try:
   fields=Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split();assert fields[19]==identity['starttime'],'producer PID reused'
   args=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
   if fields[0]=='Z':break
   assert args[:2]==[b'python3',b'tools/alu4_free_pin_cohort.py'],'producer command changed'
  except FileNotFoundError:break
  save('waiting_for_original_producer');time.sleep(10)
 receipt=json.loads((root/'receipt.json').read_text());protocol=json.loads((root/'protocol.json').read_text());assert len(receipt['reports'])==len(protocol['connection_ids'])==1012;assert sha(root/'protocol.json')==receipt['protocol_sha256'];assert sha(root/'prediction.json')==receipt['prediction_sha256'];assert all(sha(p)==h for p,h in receipt['input_sha256'].items());assert all(sha(p)==h for p,h in bindings.items());assert sha(root/'free_pin_budget_selection.py')==receipt['selector_sha256'];save('producer_terminal_complete_receipt_verified',producer_exit_status=None)
 for i,command in enumerate(commands):
  assert sha(command[1])==bindings[command[1]];save('running_stage',stage=i+1,command=command);t=time.monotonic()
  with (out/f'stage_{i+1}.log').open('w') as log:r=subprocess.run(command,cwd=plan['cwd'],env=dict(os.environ,PYTHONPATH='tools'),stdout=log,stderr=subprocess.STDOUT)
  reports.append({'command':command,'exit_status':r.returncode,'wall_s':time.monotonic()-t,'log_sha256':sha(out/f'stage_{i+1}.log')});assert r.returncode==0,f'stage {i+1} failed with exit {r.returncode}'
  if i==3:
   native=json.loads(Path('experiments/alu4_free_pin_cohort_native_analysis_2026-10-05/receipt.json').read_text());assert native['exit_code']==0 and not native['timed_out'] and native['input_hashes_unchanged'] and native['copied_route_unchanged']
 save('completed',producer_exit_status=None,scope='All audit/export/native/comparison stages completed, scientific acceptance retained by primary agent');print('postprocess queue completed',flush=True)
except Exception as exc:
 save('failed',error=f'{type(exc).__name__}: {exc}');raise
