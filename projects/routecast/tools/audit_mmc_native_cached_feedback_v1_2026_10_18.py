"""Full current MMC frame/event audits, preserving cached-floor scope limits."""
import json,sys,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from pre_route_endpoints import sha
P=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18';O=R/'experiments/mmc_native_cached_feedback_audits_v1_2026-10-18';O.mkdir(exist_ok=False);terminal=json.loads((P/'model_terminal.json').read_text());assert terminal['exit_code']==0;stages=[];start=time.perf_counter()
for stage in ['initial','sketch','events']:
 script=R/'tools'/('verify_mmc_native_feedback_events_v1_2026_10_18.py' if stage=='events' else 'verify_native_state_feedback_frame_v1_2026_10_18.py');tick=time.perf_counter()
 with (O/(stage+'.log')).open('x') as f:code=subprocess.call([sys.executable,str(script),str(P/'model'),'mmc' if stage=='events' else stage,str(O/(stage+'.json'))],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 row=dict(stage=stage,exit_code=code,seconds=time.perf_counter()-tick);stages.append(row)
 with (O/(stage+'_terminal.json')).open('x') as f:json.dump(row,f);f.write('\n')
 if code:raise SystemExit(code)
 print('MMC AUDIT PASS',stage,flush=True)
files=[Path(__file__),P/'receipt.json',R/'tools/verify_mmc_native_feedback_events_v1_2026_10_18.py',R/'tools/verify_native_state_feedback_frame_v1_2026_10_18.py'];files.extend(O.glob('*.json'))
with (O/'verification.json').open('x') as f:json.dump(dict(bindings={str(p):sha(p) for p in files},stages=stages,all_three_frame_and_complete_event_audits_pass=True,old_all_floor_independent_minimum_dual_certification=False,audit_seconds=time.perf_counter()-start,scope='Independent originalXML/Fraction complete paths/budgets/ledgers and event/price/objective/epoch replay for cached-floor correctness pilot. Old floors inherit authenticated producer/attaining-path contracts, no fresh all-old minimum proof or floor production cost. No target native routing, end-to-end gain or heldout claim.'),f,indent=2);f.write('\n')
