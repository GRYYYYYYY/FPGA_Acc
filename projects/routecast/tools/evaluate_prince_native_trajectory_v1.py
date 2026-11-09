"""All saved iterations, original gates, no selected best checkpoint or speed claim."""
import json
from pathlib import Path
from fractions import Fraction as Q
from pre_route_endpoints import sha
from external_forecast_metrics_v1 import vectors,metrics,gate
from audit_prince_forecast_metrics_v1 import check
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_native_trajectory_quality_v1_2026-10-20'
def encode(x):return json.loads(json.dumps(x,default=lambda v:dict(numerator=v.numerator,denominator=v.denominator)))
def main():
 D.mkdir(exist_ok=False);root=E/'prince_native_trajectory_v1_2026-10-20';vp=root/'trajectory_audit_verification_v1.json';v=json.loads(vp.read_text());oldp=E/'prince_feedback_quality_v1_2026-10-20/verification.json';old=json.loads(oldp.read_text());available={x['case']:x for x in old['rows']};bindings={str(p):sha(p) for p in [vp,oldp,Path(__file__)]};rows=[];checked=0
 for item in v['rows']:
  case=item['case'];proof=Path(item['proof']);assert sha(proof)==item['sha256'];audit=json.loads(proof.read_text());assert audit['all_tree_arcs_endpoints_and_NET_union_counts_verified'];bindings[str(proof)]=sha(proof)
  if case not in available:rows.append(dict(case=case,status='UNAVAILABLE_FINAL_LEGAL_LABEL',audited_snapshots=len(audit['rows'])));continue
  cp=Path(available[case]['comparison']);original=json.loads(cp.read_text());sp=cp.parent/'specification.json';s=json.loads(sp.read_text());dp=Path(s['domain_proof']);domain=json.loads(dp.read_text());rp=dp.parent/'resources.jsonl';bp=dp.parent/'spatial_bins.json';resources=list(map(json.loads,rp.open()));bins=json.loads(bp.read_text());label=Path(s['label_physical_audit']);truth={int(n):count for n,count in json.loads(label.read_text())['node_occupancy'].items()};tv=vectors(resources,bins,truth,domain['graph_nodes'],truth=True);adj={tuple(b['key']):[] for b in bins}
  for resource in resources:
   for key in resource['bins']:adj[tuple(key)].append(resource['id'])
  def normalize(ledger):return dict(resource={r['id']:Q(ledger.get(r['id'],0),r['capacity']) for r in resources},spatial={tuple(b['key']):Q(sum(ledger.get(n,0) for n in adj[tuple(b['key'])]),b['capacity']) for b in bins})
  independent_truth=normalize(truth);history=[]
  for snap in audit['rows']:
   path=Path(snap['occupancy']);assert sha(path)==snap['occupancy_sha256'];d=json.loads(path.read_text());assert d['graph_sha256']==domain['graph_sha256'];ledger={int(n):count for n,count in d['node_occupancy'].items()};m=metrics(vectors(resources,bins,ledger,domain['graph_nodes']),tv,domain['resource_k'],domain['spatial_k']);coded=encode(m);pred=normalize(ledger)
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:check(pred[scope],independent_truth[scope],k,coded[scope]);checked+=1
   checks={control:gate(m,original['metrics'][control]) for control in ['previous_native','raw_min_on']};history.append(dict(iteration=snap['iteration'],overflow_units=snap['overflow_units'],metrics=m,checks=checks,pass_both_controls=all(c['pass_primary_gate'] for c in checks.values())));bindings[str(path)]=sha(path)
  out=D/case;out.mkdir(parents=True);target=out/'trajectory_metrics.json';target.write_text(json.dumps(history,indent=2,default=lambda x:dict(numerator=x.numerator,denominator=x.denominator))+'\n');passes=[x['iteration'] for x in history if x['pass_both_controls']];rows.append(dict(case=case,status='ALL_ITERATIONS_COMPARED',iterations=len(history),all_passing_iterations=passes,earliest_passing_iteration_descriptive_only=min(passes) if passes else None,terminal_overflow=history[-1]['overflow_units'],metrics=str(target),metrics_sha256=sha(target)))
  for path in [cp,sp,dp,rp,bp,label]:bindings[str(path)]=sha(path)
  print('TRAJECTORY_METRICS',case,len(history),'passes',passes,flush=True)
 assert checked==294 and all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,independently_reconciled_metric_vectors=checked,bindings=bindings,full9_availability=False,full9_gate=False,scope='All saved native iterations compared without best-checkpoint selection. Earliest passing round is descriptive label-dependent diagnostic, not a stopping rule or promoted predictor. Snapshot instrumentation and native/audit costs paid; no rounded iteration-clock speedup or physical timing claim. Width96 missing final legal labels retained.'),indent=2)+'\n')
if __name__=='__main__':main()
