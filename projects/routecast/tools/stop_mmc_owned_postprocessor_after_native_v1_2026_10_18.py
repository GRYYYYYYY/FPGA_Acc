"""Stop only verified owned Python after last native exits, before known quadratic audit."""
from pathlib import Path
import json,os,signal,time
R=Path(__file__).resolve().parents[1];root=R/'experiments/mmc_native_seed_utility_pilot_v1_2026-10-18';meta=json.loads((R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json').read_text())['mmc_native_seed_utility_pilot_v1'];owner=meta['owners'][0];pid=owner['pid'];p=Path('/proc')/str(pid)
while True:
 if not p.exists():print('Original owner already terminal; no signal sent',flush=True);break
 stat=(p/'stat').read_text().rsplit(')',1)[1].split()
 if int(stat[19])!=owner['starttime_ticks']:raise RuntimeError('PID identity changed; no signal')
 terminal=root/'local/terminal.json'
 if terminal.exists():
  t=json.loads(terminal.read_text())
  if t['exit_status']!=0:print('Native failed; preserve original pipeline, no signal',flush=True);break
  if (root/'local/physical_audit.json').exists():print('Quadratic stage already complete; no signal',flush=True);break
  args=(p/'cmdline').read_bytes().split(b'\0');assert any(a.endswith(b'/run_mmc_native_seed_utility_pilot_v1_2026_10_18.py') for a in args)
  if (p/'task'/str(pid)/'children').read_text().strip():time.sleep(.1);continue
  os.kill(pid,signal.SIGSTOP)
  for _ in range(100):
   if (p/'stat').read_text().rsplit(')',1)[1].split()[0]=='T':break
   time.sleep(.01)
  if (p/'task'/str(pid)/'children').read_text().strip():os.kill(pid,signal.SIGCONT);time.sleep(.1);continue
  D=R/'experiments/mmc_native_postprocess_recovery_v1_2026-10-18';D.mkdir(exist_ok=False)
  with (D/'interruption.json').open('x') as f:json.dump(dict(owner=owner,local_native_terminal=t,raw_native_exit_status=0,raw_final_gate_pass=True,no_live_children=True,reason='Stop only owned Python postprocessor after all native invocations terminated; O(connections*NETs) repeated constant set construction identified in endpoint filter. Not elapsed-time cancellation; no native child interrupted; reuse successful native outputs and finish indexed audit/canonical in fresh destination.',session=85653),f,indent=2);f.write('\n')
  os.kill(pid,signal.SIGTERM);os.kill(pid,signal.SIGCONT);print('Stopped verified owned postprocessor after successful local native; all native outputs preserved',flush=True);break
 time.sleep(.1)
