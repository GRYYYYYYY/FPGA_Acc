"""Actual copied live-event demand against unchanged original forecast gates."""
import json,struct
from pathlib import Path
from fractions import Fraction as Q
from pre_route_endpoints import sha
from external_forecast_metrics_v1 import vectors,metrics,gate
from audit_prince_forecast_metrics_v1 import check
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_live_ready_quality_v1_2026-10-20'
def encode(x):return json.loads(json.dumps(x,default=lambda v:dict(numerator=v.numerator,denominator=v.denominator)))
def main():
 D.mkdir(exist_ok=False);root=E/'prince_ready_consumer_trial_v1_2026-10-20';vp=root/'ready_event_verification_v1.json';v=json.loads(vp.read_text());replay=E/'prince_forecast_ready_replay_v1_2026-10-20/verification.json';expected={x['case']:x for x in json.loads(replay.read_text())['rows']};bindings={str(q):sha(q) for q in [vp,replay,Path(__file__)]};rows=[];checked=0
 for entry in v['rows']:
  if entry['mode']!='digest':continue
  case=entry['case'];d=root/case/'digest';iteration=entry['selected_iteration'];row=dict(case=case,selected_iteration=iteration,pass_both_controls=False)
  if iteration is None:row['status']='NO_READY_EVENT_AND_NO_LEGAL_FINAL_LABEL';rows.append(row);continue
  payload=d/'callback.tsv.ready_RR.bin';raw=payload.read_bytes();i,n=struct.unpack_from('<QQ',raw,8);assert raw[:8]==b'RCBND001' and i==iteration and len(raw)==24+24*n;ledger={}
  for idx,(nid,kind,count,cap,word) in enumerate(struct.iter_unpack('<QIiiI',raw[24:])):assert nid==idx and count>=0 and cap>0;ledger[nid]=count
  specp=E/'prince_feedback_quality_v1_2026-10-20'/case/'specification.json';s=json.loads(specp.read_text());dp=Path(s['domain_proof']);domain=json.loads(dp.read_text());assert n==domain['graph_nodes'];rp=dp.parent/'resources.jsonl';bp=dp.parent/'spatial_bins.json';resources=list(map(json.loads,rp.open()));bins=json.loads(bp.read_text());label=Path(s['label_physical_audit']);truth={int(k):v for k,v in json.loads(label.read_text())['node_occupancy'].items()};result=metrics(vectors(resources,bins,ledger,n),vectors(resources,bins,truth,n,truth=True),domain['resource_k'],domain['spatial_k']);adj={tuple(b['key']):[] for b in bins}
  for r in resources:
   for key in r['bins']:adj[tuple(key)].append(r['id'])
  def normalize(values):return dict(resource={r['id']:Q(values.get(r['id'],0),r['capacity']) for r in resources},spatial={tuple(b['key']):Q(sum(values.get(n,0) for n in adj[tuple(b['key'])]),b['capacity']) for b in bins})
  a,b=normalize(ledger),normalize(truth);coded=encode(result)
  for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:check(a[scope],b[scope],k,coded[scope]);checked+=1
  cp=specp.parent/'comparison.json';original=json.loads(cp.read_text());checks={control:gate(result,original['metrics'][control]) for control in ['previous_native','raw_min_on']};passed=all(x['pass_primary_gate'] for x in checks.values());assert passed==expected[case]['pass_both_controls'];row.update(status='ACTUAL_LIVE_DEMAND_COMPARED',metrics=result,checks=checks,pass_both_controls=passed,clock=entry['clock']);rows.append(row)
  for p in [payload,specp,dp,rp,bp,label,cp]:bindings[str(p)]=sha(p)
 assert checked==12 and len(rows)==9 and all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,independent_metric_vectors=checked,pass_available_cases=sum(x['pass_both_controls'] for x in rows),available_cases=6,required_cases=9,full9_gate=False,bindings=bindings,scope='Copied live-event partial demand, original controls/ties/gates unchanged. Both primary metric implementation and independent doubled-rank/transposed aggregation reconciled. Exposed-development result only. Clocks measure observed prefix/event publication including validation; upstream/later audit/complete matched workflow gain remain open. No legal route commit, early native stop or unseen claim.'),indent=2,default=lambda x:dict(numerator=x.numerator,denominator=x.denominator))+'\n');print('LIVE_READY_QUALITY',sum(x['pass_both_controls'] for x in rows),6,checked)
if __name__=='__main__':main()
