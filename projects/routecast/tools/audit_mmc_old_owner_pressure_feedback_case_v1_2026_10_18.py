"""Independent final frame and every context-scheduled transaction audit."""
import json,sys,subprocess,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
case=sys.argv[1];assert case in ['case_01','case_02','case_03'];D=R/'experiments/mmc_old_owner_pressure_feedback_v1_2026-10-18'/case;M=D/'model';rp=M/'receipt.json';r=json.loads(rp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};O=D/'audits';O.mkdir();rows=[]
def run(stage):
 script=R/'tools'/('verify_native_endpoint_v2_feedback_frame_v1_2026_10_18.py' if stage=='sketch' else 'verify_old_owner_pressure_feedback_events_v1_2026_10_18.py');proof=O/(stage+'.json');tick=time.perf_counter()
 with (O/(stage+'.log')).open('x') as f:code=subprocess.call([sys.executable,str(script),str(M),'sketch' if stage=='sketch' else case,str(proof)],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 return dict(stage=stage,exit_code=code,seconds=time.perf_counter()-tick),proof
with ThreadPoolExecutor(max_workers=2) as pool:
 for future in as_completed([pool.submit(run,s) for s in ['sketch','events']]):
  row,proof=future.result();rows.append(row)
  with (O/'stages.jsonl').open('a') as f:f.write(json.dumps(row)+chr(10))
  if row['exit_code']==0:
   p=json.loads(proof.read_text());assert p['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];bindings[str(proof)]=sha(proof);print('CONTEXT AUDIT PASS',case,row['stage'],flush=True)
assert len(rows)==2 and all(x['exit_code']==0 for x in rows)
events=json.loads((O/'events.json').read_text());warm=json.loads((D/'warm/verification.json').read_text());assert events['events']==2*len(warm['dirty_nets']);assert sha(M/'initial.json')==sha(D/'warm/initial.json')
assert all(sha(p)==h for p,h in bindings.items())
with (O/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,events=events['events'],both_final_and_all_context_events_pass=True,initial_frame_byte_equal_independently_audited_retained_off=True,scope='Independent complete final XML/Fraction and all context-scheduled transaction replay; initial proof transferred by byte equality. No target native QoR, heldout, timing or fullworkflow gain.'),f,indent=2)
print('CONTEXT FULL AUDIT CLOSED',case,events['events'],flush=True)
