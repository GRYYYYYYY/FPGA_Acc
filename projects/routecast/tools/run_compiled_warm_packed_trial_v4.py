"""Qualification-gated, prespecified two-candidate ABBA process timing."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'compiled_warm_packed_trial_v4_2026-10-20';O=E/'xtea_placement_feedback_decisions_v1_2026-10-13'
def load(p):return json.loads(p.read_text())
def parity(folder,original):
 for n in ['initial.json','sketch.json']:assert load(folder/n)==load(original/n)
 a=load(folder/'receipt.json');b=load(original/'receipt.json');assert len(a['rounds'])==len(b['rounds'])
 for x,y in zip(a['rounds'],b['rounds']):
  assert {k:v for k,v in x.items() if k not in ['seconds','state_file']}=={k:v for k,v in y.items() if k not in ['seconds','state_file']};assert load(Path(x['state_file']))==load(Path(y['state_file']))
def main():
 protocol=load(D/'protocol.json')
 for p,h in protocol['bindings'].items():assert sha(p)==h
 parity(D/'qualification/model',O/'candidate_06/model')
 (D/'qualification_parity.json').write_text(json.dumps(dict(exact_initial_final_round_states_and_events=True,candidate_id=6))+'\n');rows=[]
 for cid in protocol['candidates']:
  source=O/f'candidate_{cid:02d}';prep=source/'prepared'
  for i,mode in enumerate(protocol['order']):
   out=D/f'candidate_{cid:02d}'/f'run_{i}_{mode}';out.mkdir(parents=True);script='run_warm_epoch_retained_update_v1.py' if mode=='baseline' else 'run_warm_compiled_context_v4.py';args=['python3',str(R/'tools'/script),str(E/f'xtea_placement_feedback_cohort_v2_2026-10-13/candidate_{cid:02d}/demand/endpoints.json'),str(out/'model'),str(prep/'base/verification.json'),str(prep/'timing'),str(prep/'warm'),'local'];start=time.perf_counter()
   with (out/'model.log').open('x') as log:code=subprocess.call(args,stdout=log,stderr=subprocess.STDOUT,cwd=R)
   elapsed=time.perf_counter()-start
   if code:raise RuntimeError((cid,mode,code))
   parity(out/'model',source/'model');rows.append(dict(candidate_id=cid,mode=mode,process_seconds=elapsed,exit_code=code,output=str(out)));(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print('PACKED_TRIAL',cid,i,mode,elapsed,flush=True)
 (D/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
