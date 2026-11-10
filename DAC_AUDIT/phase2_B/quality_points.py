"""Retain all legal points, including rejected quality regressions; annotate Pareto and target arrivals."""
from pathlib import Path
import json,csv
D=Path(__file__).resolve().parent;P=json.loads((D/'PROTOCOL.json').read_text());R=Path(P['output_root']);S=json.loads((R/'summary.json').read_text());rows=[];targets={'diffeq':(6.59759,9098),'clma':(11.5929,79926)}
for run in S['rows']:
 if run.get('status')!='completed' or run['mode'] not in ['baseline','performance']:continue
 case=run['case'];w=R/run['id'];budget=P['baseline_budgets'][case]
 if run['mode']=='baseline':
  b=json.loads((w/'baseline.json').read_text());b0=b['b0'];trials=[{'trial':t['seed'],'cpd_ns':t.get('cpd_ns'),'wirelength':t.get('wirelength'),'legal':t.get('legal',False),'time_s':t.get('validated_s',1e99),'accepted':t.get('accepted',False),'reason':t.get('reason',t.get('status'))} for t in b['trials']];arm='native_fresh_SA'
 else:
  b=json.loads((w/'report.json').read_text());o=json.loads((w/'observations.json').read_text());b0=b['baseline'];offset=max(0,run['outer_s']-o['wall_s']);trials=[{'trial':t['trial'],'cpd_ns':t['closure'].get('cpd_ns'),'wirelength':t['closure'].get('wirelength'),'legal':t['closure'].get('legal',False),'time_s':t['completed_elapsed_s']+offset,'accepted':t['accepted'],'reason':t['reason']} for t in b['trials']];arm=run['arm']
 points=[{'trial':'B0','cpd_ns':b0['cpd_ns'],'wirelength':b0['wirelength'],'legal':True,'time_s':0,'accepted':True,'reason':'retained common start'}]+trials
 for t in points:
  t.update(case=case,arm=arm,source_run=run['id'],budget_s=budget,before_cutoff=t['time_s']<=budget)
  valid=t['legal'] and t['before_cutoff'];t['pareto_legal_before_cutoff']=valid and not any(q['legal'] and q['time_s']<=budget and q['cpd_ns']<=t['cpd_ns'] and q['wirelength']<=t['wirelength'] and (q['cpd_ns']<t['cpd_ns'] or q['wirelength']<t['wirelength']) for q in points)
  t['reaches_frozen_phase2A_target']=valid and t['accepted'] and t['cpd_ns']<=targets[case][0] and t['wirelength']<=targets[case][1]
 rows+=points
with (D/'quality_points.csv').open('w',newline='') as f:
 wr=csv.DictWriter(f,list(rows[0]) if rows else ['case']);wr.writeheader();wr.writerows(rows)
print('points',len(rows))
