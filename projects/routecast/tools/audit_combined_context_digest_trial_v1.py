"""Alternative-candidate exact state/events audit and paired timing summary."""
import json,statistics
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'combined_context_digest_trial_v1_2026-10-20';O=E/'xtea_placement_feedback_decisions_v1_2026-10-13'
def load(p):return json.loads(p.read_text())
def main():
 p=load(D/'protocol.json')
 for path,h in p['bindings'].items():assert sha(path)==h
 results=load(D/'results.json');checks=[];summary=[]
 for cid in p['candidates']:
  rows=[r for r in results if r['candidate_id']==cid];assert [r['mode'] for r in rows]==p['order'];old=O/f'candidate_{cid:02d}/model';reference=load(old/'receipt.json')
  for row in rows:
   out=Path(row['output']);assert row['exit_code']==0
   for name in ['initial.json','sketch.json']:assert load(out/'model'/name)==load(old/name)
   receipt=load(out/'model/receipt.json');assert len(receipt['rounds'])==len(reference['rounds']);events=0
   for a,b in zip(receipt['rounds'],reference['rounds']):
    assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']};assert load(Path(a['state_file']))==load(Path(b['state_file']));events+=len(a['events'])
   if row['mode']=='combined':
    adapter=load(out/'factored_adapter.json');cache=load(out/'cache_stats.json');assert adapter['context_sha256']==sha(R/'tools/factored_multiplicative_context_v1.py');assert cache['stats']['hits']>0 and cache['manifest_sha256']==sha(D/f'frozen_manifest_{cid}.json')
   checks.append(dict(candidate_id=cid,output=str(out),events=events,exact_initial_final_round_states_and_events=True))
  baseline=statistics.mean(r['process_seconds'] for r in rows if r['mode']=='baseline');combined=statistics.mean(r['process_seconds'] for r in rows if r['mode']=='combined');summary.append(dict(candidate_id=cid,baseline_mean_seconds=baseline,combined_mean_seconds=combined,mean_time_reduction=1-combined/baseline))
 out=dict(status='ALL8_ALTERNATIVE_CANDIDATE_COMBINED_RUNS_EXACT_STATE_EVENT_PARITY',checks=checks,summary=summary,scope='Twoexposedmoves,2permode,cold separateprocess ABBA;not family generalization/fullpaid/native or hardware acceleration.',bindings={str(path):sha(path) for path in [D/'protocol.json',D/'results.json',Path(__file__)]})
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status']);print(summary)
if __name__=='__main__':main()
