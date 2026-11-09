"""Independent exact state/event replay audit and isolated timing summary."""
import json,statistics
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'compiled_warm_packed_trial_v4_2026-10-20';O=E/'xtea_placement_feedback_decisions_v1_2026-10-13'
def load(p):return json.loads(p.read_text())
def main():
 protocol=load(D/'protocol.json')
 for p,h in protocol['bindings'].items():assert sha(p)==h
 rows=load(D/'results.json');checks=[];summary=[]
 for cid in protocol['candidates']:
  subset=[r for r in rows if r['candidate_id']==cid];assert [r['mode'] for r in subset]==protocol['order'];original=O/f'candidate_{cid:02d}/model';reference=load(original/'receipt.json')
  for row in subset:
   model=Path(row['output'])/'model';assert row['exit_code']==0
   for n in ['initial.json','sketch.json']:assert load(model/n)==load(original/n)
   actual=load(model/'receipt.json');assert len(actual['rounds'])==len(reference['rounds']);events=0
   for a,b in zip(actual['rounds'],reference['rounds']):
    assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']};assert load(Path(a['state_file']))==load(Path(b['state_file']));events+=len(a['events'])
   checks.append(dict(candidate_id=cid,output=row['output'],events=events,exact_all_states_and_events=True))
  baseline=statistics.mean(r['process_seconds'] for r in subset if r['mode']=='baseline');packed=statistics.mean(r['process_seconds'] for r in subset if r['mode']=='packed');summary.append(dict(candidate_id=cid,baseline_mean_seconds=baseline,packed_mean_seconds=packed,mean_time_reduction=1-packed/baseline))
 out=dict(status='ALL8_COMPILED_PACKED_RUNS_STATE_EVENT_PARITY_VERIFIED',checks=checks,summary=summary,scope='2exposedmoves,2timings perarm,coldprocess ABBA. Same warm policy/ledger/path outputs;not fullworkflow/native/unseen/hardware acceleration.',bindings={str(p):sha(p) for p in [D/'protocol.json',D/'results.json',D/'guards.log',D/'qualification_parity.json',Path(__file__)]})
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status']);print(summary)
if __name__=='__main__':main()
