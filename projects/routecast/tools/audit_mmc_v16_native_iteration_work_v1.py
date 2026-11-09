"""Authenticate complete v16 iteration tables and paid workflow bounds; no rerun."""
import json,re,math
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
ROW=re.compile(r'^\s*(\d+)\s+([0-9.]+)\s+([0-9.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\(\s*([0-9.]+)%\)')
def parse(text):
 rows=[]
 for line in text.splitlines():
  m=ROW.match(line)
  if not m:continue
  f=line.split();assert [int(f[i]) for i in [0,3,4,5,6,7]]==[int(m[i]) for i in [1,4,5,6,7,8]]
  rows.append(dict(iteration=int(m[1]),printed_iteration_seconds=float(m[2]),present_factor_text=m[3],BB_updates=int(m[4]),heap_pushes=int(m[5]),rerouted_NET_operations=int(m[6]),rerouted_connection_operations=int(m[7]),overused_RR_nodes=int(m[8])))
 success=re.findall(r'Successfully routed after (\d+) routing iterations\.',text);assert len(success)==1
 assert [x['iteration'] for x in rows]==list(range(1,int(success[0])+1)) and rows[-1]['overused_RR_nodes']==0
 routing=re.findall(r'# Routing took ([0-9.]+) seconds',text);assert len(routing)==1 and 'VPR succeeded' in text
 return dict(iterations=len(rows),rows=rows,total_heap_pushes=sum(x['heap_pushes'] for x in rows),total_rerouted_NET_operations=sum(x['rerouted_NET_operations'] for x in rows),total_rerouted_connection_operations=sum(x['rerouted_connection_operations'] for x in rows),printed_routing_seconds=float(routing[0]))
def main():
 root=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10';vp=root/'verification.json';sp=root/'stage_cost_verification_v13.json';v=json.loads(vp.read_text());s=json.loads(sp.read_text());assert v['all_cases_both_complete_arms_authenticated'] and s['stage_accounting_pass']
 bindings={str(Path(__file__).resolve()):sha(Path(__file__)),str(vp):sha(vp),str(sp):sha(sp)}
 for x in [v,s]:
  for p,h in x['bindings'].items():assert sha(p)==h
 costs={x['arm']:{Path(z['log']).name if 'log' in z else z['stage']:z['seconds'] for z in x['stages']} for x in s['rows']}
 arms={}
 for mode in ['cold','seed']:
  native=root/mode/'native/mmc';receipt=json.loads((native/'receipt.json').read_text());path=native/'native.log';assert receipt['files'][str(path)]==sha(path)
  text=path.read_text();assert ('NET-aware seed imported' in text)==(mode=='seed');a=parse(text)
  physical=json.loads((native/'verification.json').read_text());assert physical['original_native_FULL_check_pass'] and physical['overflow_units']==0 and physical['physical_connections']==115572
  assert physical['iterations']==a['iterations']
  a.update(native_process_seconds=receipt['native_process_seconds'],printed_final_wirelength=receipt['wirelength'],printed_diagnostic_cpd_ns=receipt['diagnostic_cpd_ns'],continuous_arm_seconds=v[mode+'_continuous_cohort_seconds'])
  assert math.isclose(costs[mode]['native.log'],a['native_process_seconds'],rel_tol=.01)
  arms[mode]=a
  for p in [path,native/'receipt.json',native/'verification.json']:bindings[str(p)]=sha(p)
 old,new=arms['cold'],arms['seed'];delta={k:new[k]-old[k] for k in ['iterations','total_heap_pushes','total_rerouted_NET_operations','total_rerouted_connection_operations','printed_routing_seconds','native_process_seconds','printed_final_wirelength','printed_diagnostic_cpd_ns']}
 first={k:new['rows'][0][k]-old['rows'][0][k] for k in ['heap_pushes','rerouted_NET_operations','rerouted_connection_operations','overused_RR_nodes']}
 model=costs['seed']['mmc_model_native_seed.log'];audit=costs['seed']['mmc_shared_audits.log'];excess=new['continuous_arm_seconds']-old['continuous_arm_seconds']
 bounds=dict(complete_excess_seconds=excess,paid_model_handoff_seconds=model,paid_shared_audit_seconds=audit,zero_model_and_shared_audit_seed_seconds=new['continuous_arm_seconds']-model-audit,zero_native_process_alone_seed_seconds=new['continuous_arm_seconds']-new['native_process_seconds'],zero_routing_section_alone_seed_seconds=new['continuous_arm_seconds']-new['printed_routing_seconds'])
 out=R/'experiments/mmc_v16_native_iteration_work_v1_2026-10-17';out.mkdir()
 result=dict(all_pass=True,arms=arms,seed_minus_cold_total_deltas=delta,seed_minus_cold_first_iteration_deltas=first,hypothetical_bounds=bounds,bindings=bindings,scope='Authenticated printed integer iteration counters; rerouted NET/connection operations sum repeated work, not distinct identities or retained-seed survival. Rounded iteration/routing printed times differ from full native process and complete continuous arm boundaries. One exposed historical trial, no new native run, paired end-to-end benefit or causal convergence proof.',promoted=False)
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(delta=delta,first_iteration_delta=first,bounds=bounds),indent=2))
if __name__=='__main__':main()
