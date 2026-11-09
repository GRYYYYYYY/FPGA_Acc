"""Join fixed input-only stability to previously exposed native quality labels."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_ready_stability_diagnosis_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);vp=E/'prince_demand_stability_v1_2026-10-20/verification.json';v=json.loads(vp.read_text());qualityp=E/'prince_native_trajectory_quality_v1_2026-10-20/verification.json';quality={x['case']:x for x in json.loads(qualityp.read_text())['rows']};readyp=E/'prince_live_ready_quality_v1_2026-10-20/verification.json';ready={x['case']:x for x in json.loads(readyp.read_text())['rows']};bindings={str(p):sha(p) for p in [vp,qualityp,readyp,Path(__file__)]};events=[];regressions=[]
 for row in v['rows']:
  case=row['case'];sp=Path(row['proof']);assert sha(sp)==row['sha256'];stability=json.loads(sp.read_text());q=quality[case]
  if q['status']!='ALL_ITERATIONS_COMPARED':continue
  qp=Path(q['metrics']);assert sha(qp)==q['metrics_sha256'];labels=json.loads(qp.read_text());event=ready[case]['selected_iteration'];selected=labels[event-1];current=stability[event-1];assert event==selected['iteration']==current['iteration'];controls=ready[case]['checks'];failed={c:[x['metric'] for x in g['checks'] if not x['nonregress']] for c,g in controls.items()};events.append(dict(case=case,iteration=event,pass_both_controls=selected['pass_both_controls'],failed_metrics=failed,current_vs_previous=current['metrics'],spatial_spearman=selected['metrics']['spatial']['spearman'],spatial_topK_hits=selected['metrics']['spatial']['top_k_hits']))
  for index in range(1,len(labels)):
   previous,now=labels[index-1:index+1]
   if previous['pass_both_controls'] and not now['pass_both_controls']:
    regressions.append(dict(case=case,from_iteration=previous['iteration'],to_iteration=now['iteration'],overuse_units_before=previous['overflow_units'],overuse_units_after=now['overflow_units'],current_vs_previous=stability[index]['metrics']))
  bindings[str(sp)]=sha(sp);bindings[str(qp)]=sha(qp)
 assert len(events)==6 and len(regressions)==3 and all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(events=events,pass_to_fail_transitions=regressions,bindings=bindings,scope='Descriptive join on exposed development trajectories. Adjacent ranking stability is an input-only observable; final quality is a separate label. No threshold tuning, stability certificate, causal inference, unseen evidence or budget-policy promotion.'),indent=2)+'\n');print('READY_STABILITY_DIAGNOSIS',len(events),len(regressions));print([(x['case'],x['pass_both_controls'],x['current_vs_previous']['spatial']['adjacent_spearman'],x['current_vs_previous']['spatial']['retained_topK']) for x in events])
if __name__=='__main__':main()
