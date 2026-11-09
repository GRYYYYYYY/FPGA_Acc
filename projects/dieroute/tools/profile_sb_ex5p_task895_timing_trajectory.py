"""Read-only timing input/output trajectory; no rerouting or adoption."""
import csv,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'work/sb_ex5p_task895_timing_trajectory_20261015'
def main():
 P.mkdir(exist_ok=False);refs={};out=[]
 for label,relative in [('weight128','work/rr_remaining_tail_precision_development_v2_20261015/native_runs/ex5p_scale256_0'),('weight0','work/rr_remaining_tail_zero_seed_ablation_20261015/native_runs/ex5p_weight0_scale256_0')]:
  rows=[]
  for f in sorted((R/relative).glob('route.timing_iteration_*.input.csv'),key=lambda x:int(x.name.split('_')[-1].split('.')[0])):
   g=f.with_name(f.name.replace('.input.','.output.'))
   a=[x for x in csv.DictReader(f.open()) if x['task_id']=='895'];b=[x for x in csv.DictReader(g.open()) if x['task_id']=='895']
   assert len(a)==len(b)==1
   a={k:int(v) for k,v in a[0].items()};b={k:int(v) for k,v in b[0].items()}
   assert (a['net_id'],a['source'],a['sink'])==(138,43804,14256)
   assert a['delay_ps']==b['delay_ps'] and a['routed']==1
   rows.append(dict(iteration=a['iteration'],delay_ps=a['delay_ps'],input_criticality_q=a['criticality_q'],output_criticality_q=b['criticality_q'],reported_hook_CPD_ps=b['critical_path_delay_ps']))
   for path in [f,g]:refs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
  assert [v['iteration'] for v in rows]==list(range(len(rows)))
  assert len(rows)==(9 if label=='weight128' else 10)
  assert rows[-1]['output_criticality_q']==65535
  out.append(dict(case=label,trajectory=rows))
 refs[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 report=dict(status='task895_all_recorded_timing_inputs_outputs_bound',outcomes=out,source_sha256=refs,adopted=False,research_complete=False,scope='Archived hook values only; hook CPD integer is not substituted for exact final native CPD. Output/input differences can include intervening router policy. No attribution, extra-iteration benefit, causal repair or new quality result is established.')
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=report['status'],iterations=[len(v['trajectory']) for v in out])))
if __name__=='__main__':main()
