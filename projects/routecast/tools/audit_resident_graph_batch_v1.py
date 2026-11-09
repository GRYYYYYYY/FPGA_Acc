"""Independent batch-state/transaction isolation and cold timing audit."""
import json,statistics
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'resident_graph_batch_trial_v1_2026-10-20';O=E/'xtea_placement_feedback_decisions_v1_2026-10-13'
def load(p):return json.loads(p.read_text())
def main():
 protocol=load(D/'protocol.json')
 for p,h in protocol['bindings'].items():assert sha(p)==h
 rows=load(D/'results.json');assert [r['mode'] for r in rows]==protocol['order'];checks=[]
 for row in rows:
  batch=load(Path(row['output'])/'receipt.json');assert [r['candidate_id'] for r in batch['rows']]==protocol['candidate_order'];assert row['exit_code']==0
  for p,h in batch['bindings'].items():assert sha(p)==h
  if row['mode']=='resident':assert batch['cache_stats']==dict(requests=3,hits=2,misses=1)
  for item in batch['rows']:
   model=Path(item['model']);original=O/f"candidate_{item['candidate_id']:02d}/model"
   for n in ['initial.json','sketch.json']:assert load(model/n)==load(original/n)
   actual=load(model/'receipt.json');reference=load(original/'receipt.json');assert len(actual['rounds'])==len(reference['rounds']);events=0
   for a,b in zip(actual['rounds'],reference['rounds']):
    assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']};assert load(Path(a['state_file']))==load(Path(b['state_file']));events+=len(a['events'])
   checks.append(dict(batch=row['output'],candidate_id=item['candidate_id'],index=item['index'],events=events,exact_all_states_and_events=True))
 baseline=statistics.mean(r['process_seconds'] for r in rows if r['mode']=='baseline');resident=statistics.mean(r['process_seconds'] for r in rows if r['mode']=='resident');out=dict(status='ALL12_ABA_CANDIDATE_STATES_AND_EVENTS_EXACT_NO_CROSS_CANDIDATE_LEAKAGE',checks=checks,baseline_mean_seconds=baseline,resident_mean_seconds=resident,mean_time_reduction=1-resident/baseline,scope='Coldstartup included sameprocess batch ABBA,1exposeddesign,2observations permode;not endtoend/native/family/hardware gain.',bindings={str(p):sha(p) for p in [D/'protocol.json',D/'results.json',D/'guards.log',Path(__file__)]})
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status']);print(baseline,resident,out['mean_time_reduction'])
if __name__=='__main__':main()
