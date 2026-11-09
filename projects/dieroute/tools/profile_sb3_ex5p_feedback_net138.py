"""Read-only completed ex5p pair diagnosis; no whole-study or causal claim."""
import csv,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_ex5p_feedback_net138_20261015';B=R/'work/sb3_fixed_feedback_pair_20261015'
def main():
 P.mkdir(exist_ok=False);refs={}
 def sha(f):
  key=str(f)
  if key not in refs:refs[key]=hashlib.sha256(Path(f).read_bytes()).hexdigest()
  return refs[key]
 def read(f):sha(f);return json.loads(f.read_text())
 def table(f):sha(f);return list(csv.DictReader(f.open()))
 outcomes=[]
 for arm in ['feedback_off','feedback_on']:
  d=B/'native_runs'/('ex5p_'+arm+'_0');replay=read(d/'replay_audit.json')
  for f,h in replay['source_sha256'].items():assert sha(f)==h,f
  assert replay['cpu_legal'] and replay['final_resources_and_costs_byte_equivalent']
  validation=read(d/'native_validation/validation.json');assert validation['legal'] and validation['vpr_exit_status']==0
  assert sha(d/'native_validation/vpr_analysis.stdout')==validation['stdout_sha256']
  trajectory=[]
  for f in sorted(d.glob('route.timing_iteration_*.input.csv'),key=lambda x:int(x.name.split('_')[-1].split('.')[0])):
   row=next(v for v in table(f) if v['task_id']=='895');assert (row['net_id'],row['source'],row['sink'])==('138','43804','14256');trajectory.append({k:int(row[k]) for k in ['iteration','delay_ps','criticality_q','routed']})
  events=[{k:int(v) for k,v in row.items()} for row in table(d/'route.critical_feedback.csv') if row['net_id']=='138']
  outcomes.append(dict(arm=arm,task895_trajectory=trajectory,net138_feedback_events=events,native_WL=validation['total_wirelength'],native_CPD_ns=validation['critical_path_delay_ns']))
 off,on=outcomes
 assert not off['net138_feedback_events'];accepted=[v for v in on['net138_feedback_events'] if v['decision']==1];assert len(accepted)==1 and (accepted[0]['iteration'],accepted[0]['task_id'])==(8,891)
 assert any(v['iteration']==9 and v['decision']==2 for v in on['net138_feedback_events'])
 assert [v['task895_trajectory'][-1]['delay_ps'] for v in outcomes]==[954,898]
 sha(Path(__file__).resolve());report=dict(status='completed_ex5p_net138_feedback_history_and_task895_delay_bound',outcomes=outcomes,source_sha256=refs,adopted=False,research_complete=False,scope='Completed ex5p off/on pair only; all recorded replay sources rehashed and final native report bound. net138 one-use feedback triggered by task891 at iteration8, later crossing rejected as used. Task895 final packed delay falls56ps while global native CPD falls0.004ns. Routes of other nets also change; no causal CPD decomposition, all-case/repeat/heldout or physical claim.')
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(report['status'])
if __name__=='__main__':main()
