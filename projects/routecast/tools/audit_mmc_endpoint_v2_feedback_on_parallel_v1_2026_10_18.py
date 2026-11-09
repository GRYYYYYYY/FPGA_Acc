"""Both V2final frame+complete event audits; initial proof transferred by SHA."""
import json,sys,time,subprocess
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_retained_native_initializers_v1_2026-10-18';O=D/'feedback_audits';O.mkdir(exist_ok=False);execution=D/'feedback_on/receipt.json';r=json.loads(execution.read_text());assert all(sha(p)==h for p,h in r['bindings'].items());bindings={**r['bindings'],str(execution):sha(execution),str(Path(__file__)):sha(__file__)};rows=[]
tasks=[]
for mode in ['raw_min','native_retained']:
 model=D/'feedback_on'/mode
 assert sha(model/'initial.json')==sha(D/mode/'initial.json')
 for stage in ['sketch','events']:tasks.append((mode,stage))
def run(task):
 mode,stage=task;model=D/'feedback_on'/mode;script=R/'tools'/('verify_native_endpoint_v2_feedback_frame_v1_2026_10_18.py' if stage=='sketch' else 'verify_native_endpoint_v2_feedback_events_v1_2026_10_18.py');proof=O/f'{mode}_{stage}.json';start=time.perf_counter()
 with (O/f'{mode}_{stage}.log').open('x') as log:code=subprocess.call([sys.executable,str(script),str(model),'sketch' if stage=='sketch' else 'mmc',str(proof)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 return dict(mode=mode,stage=stage,exit_status=code,seconds=time.perf_counter()-start),proof
with ThreadPoolExecutor(max_workers=4) as pool:
 futures=[pool.submit(run,task) for task in tasks]
 for future in as_completed(futures):
  row,proof=future.result();rows.append(row)
  with (O/'stages.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  if row['exit_status']!=0:continue
  v=json.loads(proof.read_text());assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];bindings[str(proof)]=sha(proof);print('AUDIT PASS',row['mode'],row['stage'],flush=True)
if any(row['exit_status'] for row in rows):raise SystemExit(1)
assert all(sha(p)==h for p,h in bindings.items())
with (O/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,max_parallel_auditors=4,initial_frames_exactly_equal_independently_verified_off_inputs=True,both_final_and_all108event_audits_pass=True,budget_policy='NATIVE_ENDPOINT_ANCHORED_PROXY_V2',scope='Two matched V2feedback arms,4full independent audits plus initial originalXML/Fraction audits transferred by complete byte equality. Not native routing or new oldminimum dual certification.'),f,indent=2)
print('ALL V2 FEEDBACK AUDITS CLOSED',flush=True)
