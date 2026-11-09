"""Terminal-only interpretation of every metric and paid clock; no adoption."""
import json,hashlib
from pathlib import Path
from stream_complete_model_receipt_summary_v1 import summarize
R=Path(__file__).resolve().parents[1];T=R/'experiments/neuron_raw_floor_trial_v1_2026-10-17';C=R/'experiments/neuron_raw_floor_full_chain_v1_2026-10-17'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(p.read_text())
def gone(path):
 m=load(path);p=Path('/proc')/str(m['pid'])/'stat'
 return not p.exists() or p.read_text().rsplit(')',1)[1].split()[19]!=m['start_stat'].rsplit(')',1)[1].split()[19]
def main():
 terminal=load(C/'terminal.json');assert terminal['exit_status']==0 and terminal['full_model_all3audits_closed_admission_and_all8_metrics_completed']
 assert gone(C/'process.json') and gone(T/'process.json')
 admission=load(T/'independent_final_admission_v1.json');metrics=load(T/'metrics/verification.json')
 assert admission['all_pass'] and admission['all_original_connections']==77106 and admission['all_events']==101534
 assert admission['initial_floor_budget_delay_values_equal_floors_byte_identical'] and not admission['initial_path_and_ledger_parity_claimed']
 assert metrics['all_pass'] and metrics['independently_checked_metric_sets']==8 and not metrics['candidate_initial_metric_parity_required']
 bindings={str(Path(__file__).resolve()):sha(__file__),str(C/'terminal.json'):sha(C/'terminal.json')}
 for p in [T/'independent_final_admission_v1.json',T/'metrics/verification.json']:
  v=load(p)
  for k,h in v['bindings'].items():assert sha(k)==h
  bindings[str(p)]=sha(p)
 rows=[]
 for frame in ['initial','sketch']:
  for domain in ['concrete','spatial']:
   a=metrics['metrics']['budget1'][frame]['metrics'][domain];b=metrics['metrics']['rawfloor1'][frame]['metrics'][domain]
   assert a['universe_size']==b['universe_size'] and a['k']==b['k']
   for name in ['spearman','precision_at_k','recall_at_k','mae']:
    x,y=a[name],b[name]
    outcome='undefined' if x is None or y is None else 'equal' if x==y else 'improved' if (y<x if name=='mae' else y>x) else 'regressed'
    rows.append(dict(frame=frame,domain=domain,metric=name,baseline=x,candidate=y,outcome=outcome))
 costs={}
 for name in ['model','initial_audit','sketch_audit','event_audit']:
  p=T/(name+'_terminal.json');v=load(p);assert v['exit_status']==0 and not v['timed_out'];costs[name]=v['seconds'];bindings[str(p)]=sha(p)
 for name in ['admit','metrics']:
  p=C/(name+'_terminal.json');v=load(p);assert v['exit_status']==0 and not v['timed_out'];costs[name]=v['seconds'];bindings[str(p)]=sha(p)
 receipt=summarize(T/'model/receipt.json');bindings[str(T/'model/receipt.json')]=sha(T/'model/receipt.json')
 phases={k:receipt['timers'][k] for k in ['model_setup_seconds','initial_seconds','feedback_seconds']}
 assert abs(sum(phases.values())-receipt['timers']['total_paid_resident_seconds'])<1
 work={}
 for name in ['initial_floor_work.json','compiled_primary_work.json','quotient_cache_cost.json','floor_engine_release.json']:
  p=T/'model'/name;bindings[str(p)]=sha(p);work[name]=load(p)
 result=dict(bindings=bindings,full_trial_complete=True,all8_metric_sets_reported=True,outcomes=rows,stage_seconds=costs,sum_disjoint_child_stage_seconds=sum(costs.values()),model_inner_disjoint_phases=phases,complete_round_statistics=receipt['rounds'],initial_and_feedback_work_reports=work,decision='Retain development-only result, report every regression and changed initial path; no default promotion or global goal completion.',scope='Paid child-stage sum excludes between-stage source checks/driver gaps and all native routing, so is not a continuous workflow clock. Model phases/search/cache timers are nested, not additional costs. Archived baseline times are unpaired; no stable speedup, full end-to-end net gain, heldout or hardware claim.',promoted=False,goal_complete=False)
 with (T/'research_decision_v1.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(dict(stage_seconds=costs,model_phases=phases,outcomes=rows),indent=2))
if __name__=='__main__':main()
