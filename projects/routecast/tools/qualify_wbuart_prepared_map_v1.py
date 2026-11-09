"""Independent full-model implementation-equivalence/performance qualification."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
from run_wbuart_prepared_map_feedback_v1 import predict
from bound_allnet_map_query_v2 import Query
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_prepared_map_preflight_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 contract=E/'prepared_map_tree_contract_v1_2026-10-20/verification.json';assert all(sha(p)==h for p,h in read(contract)['bindings'].items());D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/prepared_map_tree_bridge_v1.py',R/'tools/prepared_map_budget_repair_v1.py',R/'tools/run_wbuart_prepared_map_feedback_v1.py',contract];bindings={str(p):sha(p) for p in files};(D/'protocol.json').write_text(json.dumps({'state':'FROZEN_IMPLEMENTATION_EQUIVALENCE_NOT_STRATEGY_VARIANT','bindings':bindings,'invariant':'Same priority float32 math, masks, exact tree/G/raw, budget repair, all original gates; all full states/events/criticalities/repair records must equal scalar preflights. Existing full9 batch unchanged.','cost_scope':'Separate Query validation timing and total process wall plus instrumented predict components; not a balanced full workflow speedup proof.'},indent=2)+'\n');c=read(E/'wbuart_forecasts_v1_2026-10-20/manifest.json')['cases'][0];timing=E/'wbuart_frame_timings_v1_2026-10-20'/c['case']/'initial_connection_criticalities.json';digest=next(x['payload_sha256'] for x in read(E/'wbuart_allnet_map_batch_v1_2026-10-20/independent_matrix_verification_v1.json')['rows'] if x['case']==c['case']);rows=[]
 for mode,oldfolder in [('H0','wbuart_map_priority_control_v1_2026-10-20/H0'),('MAP','wbuart_map_priority_nonzero_v1_2026-10-20/MAP')]:
  start=time.perf_counter();q=Query(E/'wbuart_allnet_map_preflight_v1_2026-10-20/on/allmap.bin',c['endpoint'],timing,digest);load_seconds=time.perf_counter()-start;out=D/mode;predict(c['endpoint'],out,c['node_base_proof'],c['timing_directory'],Path(c['warm_directory'])/'native_retained','all',timing_policy='warm_timing_round_updated',map_query=q,priority_mode=mode);q.close();old=E/oldfolder
  for name in ['initial.json','round0.json','round1.json','sketch.json','primary_budget_repairs.json']:assert read(out/name)==read(old/name),name
  a,b=read(out/'receipt.json'),read(old/'receipt.json');assert [r['events'] for r in a['rounds']]==[r['events'] for r in b['rounds']];assert a['heuristic_calls']==b['heuristic_calls']
  for i in [0,1]:assert read(out/f'timing_round{i}.json')['criticalities']==read(old/f'timing_round{i}.json')['criticalities']
  with (D/(mode+'_audit.log')).open('x') as f:subprocess.run([sys.executable,str(R/'tools/verify_wbuart_fixed_nominal_feedback_events_v1.py'),str(out),c['case']+'_'+mode+'_prepared',str(out/'complete_event_audit.json')],stdout=f,stderr=subprocess.STDOUT,check=True)
  rows.append({'mode':mode,'query_validate_load_seconds':load_seconds,'resident_seconds':a['total_paid_resident_seconds'],'heuristic_seconds':a['heuristic_seconds'],'scalar_resident_seconds':b['total_paid_resident_seconds'],'all_states_events_timing_repairs_equal':True,'case_complete_seconds_including_audit':time.perf_counter()-start});print(mode,'PREPARED_FULL_PARITY_PASS',rows[-1],flush=True)
  for p in [out/'receipt.json',out/'complete_event_audit.json',old/'receipt.json']:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps({'status':'FIRST_CASE_PREPARED_H0_MAP_FULL_TRAJECTORY_AND_COMPLETE_AUDIT_PASS','rows':rows,'bindings':bindings,'scope':'Single-case implementation equivalence and component timing only; original9-case scalar batch unchanged, no quality/policy/native/paid gain claim.'},indent=2)+'\n')
if __name__=='__main__':main()
