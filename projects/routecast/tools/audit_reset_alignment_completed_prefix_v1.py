"""Authenticate all completed bounded receipts, every fully logged witness row."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/supported_reset_alignment_cohort_v1_2026-10-10';raw=(S/'rows.json').read_bytes();rows=json.loads(raw);D=R/'experiments/reset_alignment_completed_prefix_v1_2026-10-10';assert not D.exists();D.mkdir();(D/'observed_rows.json').write_bytes(raw);bindings={str(x):sha(x) for x in [Path(__file__).resolve(),D/'observed_rows.json']};results=[]
for row in rows:
 p=Path(row['receipt']);v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());assert row['exit_code']==v['exit_code'];lp=p.parent/'equivalence.log';text=lp.read_text();bindings.update({str(x):sha(x) for x in [p,lp]});success='SAT proof finished - no model found: SUCCESS!' in text;failure='SAT proof finished - model found: FAIL!' in text;assert success==v['reset_alignment_sat_success'];trace=[]
 for line in text.splitlines():
  m=re.match(r'^\s*(\d+)\s+\\(\S+)\s+(-?\d+|--)\s+(\S+)\s+([01x]+)\s*$',line)
  if m:trace.append(dict(step=int(m[1]),signal=m[2],binary=m[5]))
 lookup={(x['step'],x['signal']):x['binary'] for x in trace};mismatches=[]
 for (step,signal),bits in lookup.items():
  if step<3 or not signal.startswith('gate_'):continue
  other=lookup.get((step,'gold_'+signal[5:]))
  if other is not None and other!=bits:mismatches.append(dict(step=step,port=signal[5:],gate=bits,gold=other))
 results.append(dict(name=row['name'],exit_code=v['exit_code'],bounded_success=success,actual_sat_counterexample=failure,all_complete_logged_trace_rows=trace,all_logged_post_reset_output_mismatches=mismatches))
assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=results,whole4_complete=len(rows)==4,scope='Completed receipt prefix only, exact original source/output hashes, every complete trace row and pairwise output mismatch. Bounded six-step contract, not full induction or initial-state correspondence/native/family admission. Partial trace output cannot establish absent later mismatches.'),indent=2)+'\n');print([(x['name'],x['exit_code'],x['bounded_success'],len(x['all_logged_post_reset_output_mismatches'])) for x in results]);print([(x['name'],x['all_logged_post_reset_output_mismatches'][:4]) for x in results])
