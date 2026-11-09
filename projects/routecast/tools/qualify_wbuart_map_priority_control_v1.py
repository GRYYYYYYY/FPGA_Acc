"""H0 full-model control first; no weighted run before complete audit/parity."""
import json,subprocess,sys,hashlib
from pathlib import Path
from run_wbuart_map_priority_feedback_v1 import predict
from bound_allnet_map_query_v2 import Query
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_map_priority_control_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);proof=E/'wbuart_allnet_map_batch_v1_2026-10-20/independent_matrix_verification_v1.json';pr=read(proof);assert all(sha(p)==h for p,h in pr['bindings'].items());c=read(E/'wbuart_forecasts_v1_2026-10-20/manifest.json')['cases'][0];row=next(x for x in pr['rows'] if x['case']==c['case']);matrix=E/'wbuart_allnet_map_preflight_v1_2026-10-20/on/allmap.bin';timing=E/'wbuart_frame_timings_v1_2026-10-20'/c['case']/'initial_connection_criticalities.json';q=Query(matrix,c['endpoint'],timing,row['payload_sha256']);out=D/'H0';predict(c['endpoint'],out,c['node_base_proof'],c['timing_directory'],Path(c['warm_directory'])/'native_retained','all',timing_policy='warm_timing_round_updated',map_query=q,priority_mode='H0');q.close()
 with (D/'audit.log').open('x') as f:subprocess.run([sys.executable,str(R/'tools/verify_wbuart_fixed_nominal_feedback_events_v1.py'),str(out),c['case']+'_H0',str(out/'complete_event_audit.json')],stdout=f,stderr=subprocess.STDOUT,check=True)
 old=Path(next(a['output'] for r in read(E/'wbuart_forecasts_v1_2026-10-20/verification.json')['rows'] if r['case']==c['case'] for a in r['arms'] if a['initializer']=='native_retained' and a['timing_policy']=='warm_timing_round_updated'))
 for name in ['initial.json','round0.json','round1.json','sketch.json','primary_budget_repairs.json']:assert read(out/name)==read(old/name),name
 assert [r['events'] for r in read(out/'receipt.json')['rounds']]==[r['events'] for r in read(old/'receipt.json')['rounds']]
 for i in [0,1]:assert read(out/f'timing_round{i}.json')['criticalities']==read(old/f'timing_round{i}.json')['criticalities']
 files=[Path(__file__),proof,out/'complete_event_audit.json',out/'receipt.json'];(D/'verification.json').write_text(json.dumps({'status':'FIRST_ALLNET_TWO_ROUND_H0_FULL_STATE_EVENT_REPAIR_TIMING_PARITY_AND_AUDIT_PASS','bindings':{str(p):sha(p) for p in files},'weighted_run_pending':True},indent=2)+'\n');print('FULL_MODEL_H0_PASS',flush=True)
if __name__=='__main__':main()
