"""Replay one frozen label-independent ready rule, then separately join quality."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from prince_forecast_ready_gate_v1 import ReadyGate
from external_forecast_metrics_v1 import gate
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_forecast_ready_replay_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);pp=E/'prince_forecast_ready_gate_design_v1_2026-10-20/protocol.json';p=json.loads(pp.read_text());assert all(sha(f)==h for f,h in p['bindings'].items());bindings={str(pp):sha(pp),str(Path(__file__)):sha(__file__)};root=E/'prince_configured_consumer_trial_v1_2026-10-20';v=json.loads((root/'verification.json').read_text());decisions=[]
 for row in v['rows']:
  if not row['case'].endswith('/digest'):continue
  case=row['case'].rsplit('/',1)[0];d=root/row['case'];identity=dict(zip(['graph','netlist','placement','binary','phase','case','launch_config'],(d/'identity.txt').read_text().splitlines()));identity['resolved_config']=(d/'callback.tsv.resolved.sha256').read_text().strip();controller=ReadyGate(identity);selected=None;events=[]
  for line in (d/'callback.tsv').read_text().splitlines():
   t=list(map(int,line.split()));event=controller.observe(identity,t[0],t[1],t[4]);events.append(dict(iteration=t[0],nodes=t[1],overused_nodes=t[4],ready_event=event))
   if event:assert selected is None;selected=t[0]
  decisions.append(dict(case=case,selected_iteration=selected,events=events));
  for f in [d/'callback.tsv',d/'identity.txt',d/'callback.tsv.resolved.sha256']:bindings[str(f)]=sha(f)
 # Bind complete decisions before opening target quality metrics.
 dp=D/'decisions.json';dp.write_text(json.dumps(dict(rows=decisions,bindings=bindings,scope='Selection reads current native counters/identity only; prior development labels historically exposed.'),indent=2)+'\n');bindings[str(dp)]=sha(dp);rows=[]
 qualityp=E/'prince_native_trajectory_quality_v1_2026-10-20/verification.json';quality=json.loads(qualityp.read_text());bycase={x['case']:x for x in quality['rows']};bindings[str(qualityp)]=sha(qualityp)
 for d in decisions:
  case=d['case'];iteration=d['selected_iteration'];q=bycase[case];row=dict(case=case,selected_iteration=iteration,pass_both_controls=False)
  if q['status']!='ALL_ITERATIONS_COMPARED':row['status']='UNAVAILABLE_FINAL_LEGAL_LABEL'
  elif iteration is None:row['status']='NO_READY_EVENT'
  else:
   path=Path(q['metrics']);assert sha(path)==q['metrics_sha256'];m=json.loads(path.read_text())[iteration-1];assert m['iteration']==iteration;originalp=E/'prince_feedback_quality_v1_2026-10-20'/case/'comparison.json';original=json.loads(originalp.read_text());checks={c:gate(m['metrics'],original['metrics'][c]) for c in ['previous_native','raw_min_on']};passed=all(x['pass_primary_gate'] for x in checks.values());assert passed==m['pass_both_controls'];row.update(status='READY_DEMAND_COMPARED',pass_both_controls=passed,overflow_units=m['overflow_units'],checks=checks);bindings[str(path)]=sha(path);bindings[str(originalp)]=sha(originalp)
  rows.append(row);print('READY_REPLAY',case,iteration,row['status'],row['pass_both_controls'],flush=True)
 assert len(rows)==9 and all(sha(f)==h for f,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,available_targets=6,required_targets=9,passed_available_targets=sum(x['pass_both_controls'] for x in rows),full9_gate=False,scope='One fixed exposed-development forecast-readiness rule, no per-case best-round selection. Selected historical demand metrics previously independently reconciled. No native stop/commit, prefix cost/full-flow gain or unseen evidence.'),indent=2)+'\n')
if __name__=='__main__':main()
