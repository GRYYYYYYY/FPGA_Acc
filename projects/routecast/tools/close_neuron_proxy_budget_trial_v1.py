"""Bind complete causal development outcome without selecting a default on mixed metrics."""
import json,hashlib
from pathlib import Path
from observe_neuron_scaled_present_pipeline_v1 import process
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def main():
 trial=R/'experiments/neuron_proxy_budget_trial_v2_2026-10-17';chain=R/'experiments/neuron_proxy_budget_full_chain_v2_2026-10-17'
 terminal=json.loads((chain/'terminal.json').read_text());assert terminal['exit_status']==0 and terminal['full_model_all3audits_closed_admission_and_all8_metrics_completed']
 for root,name in [(chain,'process.json'),(trial,'process.json'),(trial,'model_process.json'),(chain,'metrics_process.json')]:
  m=json.loads((root/name).read_text());assert not process(m['pid'],int(m['start_stat'].rsplit(')',1)[1].split()[19]),m['args']).get('verified_live')
 admission=json.loads((trial/'independent_final_admission_v1.json').read_text());metrics=json.loads((trial/'metrics/verification.json').read_text());assert admission['all_pass'] and metrics['all_pass'] and metrics['independently_checked_metric_sets']==8
 bindings={**admission['bindings'],**metrics['bindings']};assert all(sha(p)==h for p,h in bindings.items())
 result={}
 for domain in ['concrete','spatial']:
  old=metrics['metrics']['continued1']['sketch']['metrics'][domain];new=metrics['metrics']['budget1']['sketch']['metrics'][domain]
  assert metrics['metrics']['continued1']['initial']['metrics'][domain]==metrics['metrics']['budget1']['initial']['metrics'][domain]
  result[domain]={k:dict(control=old[k],candidate=new[k],delta=new[k]-old[k]) for k in ['spearman','precision_at_k','recall_at_k','mae']}
 costs={}
 for name in ['model','initial_audit','sketch_audit','event_audit']:
  path=trial/(name+'_terminal.json');x=json.loads(path.read_text());assert x['exit_status']==0 and not x['timed_out'];costs[name]=x['seconds'];bindings[str(path)]=sha(path)
 for name in ['admit','metrics']:
  path=chain/(name+'_terminal.json');x=json.loads(path.read_text());assert x['exit_status']==0 and not x['timed_out'];costs[name]=x['seconds'];bindings[str(path)]=sha(path)
 costs['evaluation_internal_seconds']=metrics['evaluation_seconds']
 costs['note']='Metrics external process includes authentication and setup; internal evaluation is nested. Historical independent runs are unpaired and not continuous native workflow benefit.'
 for p in [Path(__file__).resolve(),chain/'terminal.json',trial/'independent_final_admission_v1.json',trial/'metrics/verification.json',trial/'cost_report_scope_annotation_v1.json',R/'experiments/neuron_proxy_budget_memory_watch_v1_2026-10-17/failure_accounting_v1.json']:bindings[str(p)]=sha(p)
 decision=dict(full_trial_complete=True,all_original_connections=77106,all_events=101534,all_three_audits_closed_admission_all8_metrics_pass=True,comparison=result,spatial_top20_hits=dict(control_final=0,candidate_final=6,common_initial=10),overflow=dict(control=4099,candidate=2209),costs=costs,decision='Mixed development result; do not promote default configuration. Spatial hotspot improves from0/20 to6/20, still below initial10/20; both MAEs and concrete precision improve, both Spearman correlations regress.',scope='Single exposed development design, bounded proxy-budget intervention. No robust multi-family unseen generalization, native timing legality/QoR, paired continuous end-to-end benefit or full graph FPGA proof.',next_action='Independently compare complete final path/NET edge unions and original-budget allowance use, then explain final hotspot overlap and high-fanout ownership under unchanged metrics. Preserve regressions; no label-driven retuning.',bindings=bindings,promoted=False,goal_complete=False)
 out=trial/'research_decision_v1.json';assert not out.exists();out.write_text(json.dumps(decision,indent=2)+'\n');print(json.dumps({k:decision[k] for k in ['comparison','spatial_top20_hits','overflow','costs','decision']},indent=2))
if __name__=='__main__':main()
