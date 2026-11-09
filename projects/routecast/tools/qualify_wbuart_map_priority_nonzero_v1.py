"""First nonzero weighted MAP full-model case, gated by terminal H0 proof."""
import json,subprocess,sys
from pathlib import Path
from run_wbuart_map_priority_feedback_v1 import predict
from bound_allnet_map_query_v2 import Query
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_map_priority_nonzero_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 control=E/'wbuart_map_priority_control_v1_2026-10-20/verification.json';v=read(control);assert v['status']=='FIRST_ALLNET_TWO_ROUND_H0_FULL_STATE_EVENT_REPAIR_TIMING_PARITY_AND_AUDIT_PASS';assert all(sha(p)==h for p,h in v['bindings'].items());design=E/'wbuart_map_priority_full_design_v1_2026-10-20/protocol.json';assert all(sha(p)==h for p,h in read(design)['bindings'].items());D.mkdir(exist_ok=False);c=read(E/'wbuart_forecasts_v1_2026-10-20/manifest.json')['cases'][0];proof=E/'wbuart_allnet_map_batch_v1_2026-10-20/independent_matrix_verification_v1.json';row=next(x for x in read(proof)['rows'] if x['case']==c['case']);timing=E/'wbuart_frame_timings_v1_2026-10-20'/c['case']/'initial_connection_criticalities.json';q=Query(E/'wbuart_allnet_map_preflight_v1_2026-10-20/on/allmap.bin',c['endpoint'],timing,row['payload_sha256']);out=D/'MAP';predict(c['endpoint'],out,c['node_base_proof'],c['timing_directory'],Path(c['warm_directory'])/'native_retained','all',timing_policy='warm_timing_round_updated',map_query=q,priority_mode='MAP');q.close()
 with (D/'audit.log').open('x') as f:subprocess.run([sys.executable,str(R/'tools/verify_wbuart_fixed_nominal_feedback_events_v1.py'),str(out),c['case']+'_MAP',str(out/'complete_event_audit.json')],stdout=f,stderr=subprocess.STDOUT,check=True)
 files=[Path(__file__),design,control,out/'complete_event_audit.json',out/'receipt.json'];(D/'verification.json').write_text(json.dumps({'status':'FIRST_ALLNET_NONZERO_MAP_TWO_ROUND_COMPLETE_EVENT_AUDIT_PASS','bindings':{str(p):sha(p) for p in files},'quality_evaluation_pending':True,'all9_batch_pending':True},indent=2)+'\n');print('FIRST_ALLNET_MAP_PASS',flush=True)
if __name__=='__main__':main()
