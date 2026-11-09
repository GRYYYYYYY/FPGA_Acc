"""Single-owner evaluation chain: no predictor restart and no duplicate output."""
import sys,time,json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
pid=int(sys.argv[1]);parent=Path('experiments/koios_cpp_resume_2026-10-05');target=Path('experiments/koios_cpp_resume_evaluation_2026-10-05');state=parent/'evaluation_chain.json'
proc=Path(f'/proc/{pid}');start=(proc/'stat').read_text().split()[21];assert b'tools/koios_cpp_resume.py' in (proc/'cmdline').read_bytes()
source_files=['evaluate_koios_cpp_resume.py','stream_metric_domain.py','prediction_metrics.py','pre_route_endpoints.py'];frozen={name:sha(Path('tools')/name) for name in source_files};command=[sys.executable,'-u','tools/evaluate_koios_cpp_resume.py'];status={'baseline_pid':pid,'baseline_proc_start':start,'command':command,'source_sha256':frozen,'policy':'one evaluation launch after baseline PID terminal and complete audited receipt; no automatic recovery/restart','status':'waiting_for_baseline'}
state.write_text(json.dumps(status,indent=2)+'\n')
while proc.exists():
 try:
  if (proc/'stat').read_text().split()[21]!=start:break
 except FileNotFoundError:break
 time.sleep(15)
if not (parent/'receipt.json').exists():
 status.update(status='baseline_terminal_without_receipt');state.write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status),flush=True);raise SystemExit(1)
assert all(sha(Path('tools')/name)==s for name,s in frozen.items());r=json.loads((parent/'receipt.json').read_text());p=json.loads((parent/'protocol.json').read_text());assert r['protocol_sha256']==sha(parent/'protocol.json') and r['audit']['requested']==15138 and r['audit']['all_physical_and_union_checks_passed'];assert all(sha(parent/n)==s for n,s in r['outputs'].items());assert not target.exists();status.update(status='evaluator_running',baseline_receipt_sha256=sha(parent/'receipt.json'));state.write_text(json.dumps(status,indent=2)+'\n');print(json.dumps({'stage':'evaluator_launch','baseline_receipt_sha256':status['baseline_receipt_sha256']}),flush=True)
with (parent/'evaluation_chain_stdout.log').open('w') as log:result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
status.update(status='terminal',evaluator_exit_code=result.returncode,stdout_sha256=sha(parent/'evaluation_chain_stdout.log'));state.write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status),flush=True);raise SystemExit(result.returncode)
