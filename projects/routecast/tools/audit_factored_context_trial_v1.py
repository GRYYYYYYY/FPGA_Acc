"""Independent whole-state and event parity, factored context ABBA timing."""
import json,hashlib,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/factored_context_trial_v1_2026-10-20';O=R/'experiments/xtea_placement_feedback_decisions_v1_2026-10-13/candidate_01/model'
def load(p):return json.loads(p.read_text())
def main():
 protocol=load(D/'protocol.json')
 for p,h in protocol['bindings'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
 rows=load(D/'results.json');assert [r['mode'] for r in rows]==protocol['order'];original=load(O/'receipt.json');checks=[]
 for row in rows:
  folder=Path(row['output']);model=folder/'model';assert row['exit_code']==0
  for name in ['initial.json','sketch.json']:assert load(model/name)==load(O/name)
  actual=load(model/'receipt.json');assert len(actual['rounds'])==len(original['rounds']);events=0
  for a,b in zip(actual['rounds'],original['rounds']):
   assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']};assert load(Path(a['state_file']))==load(Path(b['state_file']));events+=len(a['events'])
  if row['mode']=='factored':
   adapter=load(folder/'adapter.json');assert adapter['adapter_sha256']==hashlib.sha256((R/'tools/run_factored_context_session_v1.py').read_bytes()).hexdigest();assert adapter['context_sha256']==hashlib.sha256((R/'tools/factored_multiplicative_context_v1.py').read_bytes()).hexdigest()
  checks.append(dict(output=str(folder),exact_states_and_events=True,events=events))
 a=[r['process_seconds'] for r in rows if r['mode']=='baseline'];b=[r['process_seconds'] for r in rows if r['mode']=='factored'];out=dict(status='ALL4_FACTORED_TRIAL_STATES_AND_EVENTS_EXACTLY_MATCH_FROZEN_CANDIDATE',checks=checks,baseline_seconds=a,factored_seconds=b,baseline_mean=statistics.mean(a),factored_mean=statistics.mean(b),mean_relative_time_reduction=1-statistics.mean(b)/statistics.mean(a),scope='Oneexposedcandidate,2observations perarm.Producer process only;not fullpaid/netnative/unseen/hardware benefit.',bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'protocol.json',D/'results.json',D/'guards.log',Path(__file__)]})
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status']);print(out['baseline_mean'],out['factored_mean'],out['mean_relative_time_reduction'])
if __name__=='__main__':main()
