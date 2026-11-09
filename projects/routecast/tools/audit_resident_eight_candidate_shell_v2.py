"""Original eight-move choices plus exact states/events and RSS evidence."""
import json,statistics
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'resident_eight_candidate_shell_v2_2026-10-20';O=E/'xtea_placement_feedback_decisions_v1_2026-10-13'
def load(p):return json.loads(p.read_text())
def main():
 protocol=load(D/'protocol.json')
 for p,h in protocol['bindings'].items():assert sha(p)==h
 rows=load(D/'results.json');assert [r['mode'] for r in rows]==protocol['order'];old=load(O/'decision.json');frozen={r['candidate_id']:r for r in old['rows']};checks=[];events_total=0
 for row in rows:
  batch=load(Path(row['output'])/'receipt.json');assert row['exit_code']==0 and batch['peak_RSS_KiB']==row['peak_RSS_KiB'] and row['peak_RSS_KiB']>0
  for p,h in batch['bindings'].items():assert sha(p)==h
  if row['mode']=='resident':assert batch['cache_stats']==dict(requests=8,hits=7,misses=1)
  assert [r['candidate_id'] for r in batch['rows']]==list(range(9));independent=[]
  for item in batch['rows']:
   cid=item['candidate_id']
   assert item['hpwl']==frozen[cid]['hpwl']
   if cid==0:independent.append(dict(candidate_id=0,hpwl=item['hpwl'],sketch_overflow=frozen[0]['sketch_overflow']));continue
   model=Path(item['model']);reference=O/f'candidate_{cid:02d}/model'
   for name in ['initial.json','sketch.json']:assert load(model/name)==load(reference/name)
   actual=load(model/'receipt.json');original=load(reference/'receipt.json');assert len(actual['rounds'])==len(original['rounds']);events=0
   for a,b in zip(actual['rounds'],original['rounds']):
    assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']};assert load(Path(a['state_file']))==load(Path(b['state_file']));events+=len(a['events'])
   overflow=load(model/'sketch.json')['overflow_units'];assert overflow==item['sketch_overflow']==frozen[cid]['sketch_overflow'];independent.append(dict(candidate_id=cid,hpwl=item['hpwl'],sketch_overflow=overflow));events_total+=events;checks.append(dict(batch=row['output'],candidate_id=cid,events=events,exact_all_states_and_events=True))
  key=lambda r:(r['hpwl'],r['candidate_id']);admitted=[r for r in independent if r['sketch_overflow']<=independent[0]['sketch_overflow']];off=min(independent,key=key)['candidate_id'];on=min(admitted,key=key)['candidate_id'];assert off==batch['off_candidate']==old['off_candidate']==1 and on==batch['on_candidate']==old['on_candidate']==8;assert [r['candidate_id'] for r in admitted]==batch['on_admitted_candidates']==[0,4,6,8]
 summary={}
 for mode in ['baseline','resident']:
  a=[r for r in rows if r['mode']==mode];summary[mode]=dict(mean_process_seconds=statistics.mean(r['process_seconds'] for r in a),peak_RSS_KiB=[r['peak_RSS_KiB'] for r in a],mean_peak_RSS_KiB=statistics.mean(r['peak_RSS_KiB'] for r in a))
 out=dict(status='ALL32_CANDIDATES_FULLSTATE_EVENT_AND_ORIGINAL_SHELL_SELECTION_PARITY',checks=checks,events=events_total,summary=summary,mean_time_reduction=1-summary['resident']['mean_process_seconds']/summary['baseline']['mean_process_seconds'],off_candidate=1,on_candidate=8,original_full9_gate=False,scope='Twoobservations permode,oneexposeddesign. Samecompiled SKETCHon shell with/without graphreuse;not SKETCHon/off native/fullpaid/FPGA gain.',bindings={str(p):sha(p) for p in [D/'protocol.json',D/'results.json',Path(__file__)]})
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status']);print(summary);print('time_reduction',out['mean_time_reduction'])
if __name__=='__main__':main()
