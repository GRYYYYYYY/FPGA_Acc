"""Full-arm completeness, prefix parity and cumulative model component work."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_fixed_horizon_trial_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert read(D/'terminal.json')['all_pass'];m=read(D/'manifest.json');metric=read(D/'independent_metrics_verification_v1.json');old=read(E/'wbuart_forecasts_v1_2026-10-20/verification.json');rows=[];events=0;bindings={str(p):sha(p) for p in [Path(__file__),D/'manifest.json',D/'terminal.json',D/'independent_metrics_verification_v1.json']}
 for c in m['cases']:
  caseproof=read(Path(c['output'])/'verification.json')
  for arm in caseproof['arms']:
   out=Path(arm['output']);audit=read(arm['audit']);assert all(sha(n)==h for n,h in audit['bindings'].items());receipt=read(out/'receipt.json');assert len(receipt['rounds'])==16 and audit['events']==17184;events+=audit['events'];prior=Path(next(a['output'] for r in old['rows'] if r['case']==c['case'] for a in r['arms'] if a['initializer']==arm['initializer'] and a['timing_policy']==arm['timing_policy']));oldreceipt=read(prior/'receipt.json');assert [r['events'] for r in receipt['rounds'][:2]]==[r['events'] for r in oldreceipt['rounds']]
   for f in ['initial.json','round0.json','round1.json']:assert read(out/f)==read(prior/f)
   costs={}
   for h in [2,4,8,16]:
    rounds=receipt['rounds'][:h];es=[e for r in rounds for e in r['events']];costs[str(h)]={'NET_events':len(es),'primary_search_calls':sum(e['primary_search_calls'] for e in es),'commits':sum(e['status']=='COMMITTED' for e in es),'sum_recorded_round_component_seconds':sum(r['seconds'] for r in rounds),'ending_overflow_units':rounds[-1]['overflow_after']}
   rows.append({'case':c['case'],'initializer':arm['initializer'],'timing_policy':arm['timing_policy'],'prefix_work':costs,'reported_resident_component_seconds':receipt['total_paid_resident_seconds']});bindings[arm['audit']]=sha(arm['audit'])
 assert len(rows)==36 and events==618624
 (D/'work_review_v1.json').write_text(json.dumps({'status':'ALL36_ARMS618624_EVENTS_PREFIX_PARITY_AND_COMPONENT_WORK_REVIEWED','rows':rows,'events':events,'pass_counts':metric['pass_counts'],'bindings':bindings,'scope':'Round seconds/search calls are model components, not matched full paid pipeline latency or comparable native operations. Input/source/warm/first-preflight/audits and hardware transfers remain costs; no sum of independent clocks as measured end-to-end gain. No best-prefix selection.'},indent=2)+'\n');print('ALL36_ARMS618624_EVENTS_PREFIX_PARITY_AND_COMPONENT_WORK_REVIEWED')
if __name__=='__main__':main()
