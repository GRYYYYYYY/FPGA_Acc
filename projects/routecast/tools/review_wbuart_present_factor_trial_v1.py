"""Terminal completeness, exact controls and intra-schedule round0 timing parity."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_present_factor_trial_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 terminal=read(D/'terminal.json');assert terminal['all_pass'] and len(terminal['rows'])==9;m=read(D/'manifest.json');metrics=read(D/'independent_metrics_verification_v1.json');assert metrics['metric_vectors']==54 and len(metrics['rows'])==18;old=read(E/'wbuart_forecasts_v1_2026-10-20/verification.json');bindings={str(p):sha(p) for p in [Path(__file__),D/'manifest.json',D/'terminal.json',D/'independent_metrics_verification_v1.json']};rows=[];events=0
 for c in m['cases']:
  arms=read(Path(c['output'])/'verification.json')['arms'];assert len(arms)==4
  for arm in arms:
   for role,key,expected in [('control','control_output',[[1,1],[1,1]]),('candidate','candidate_output',[[0,1],[1,2]])]:
    out=Path(arm[key]);audit=read(out/'complete_event_audit.json');assert all(sha(p)==h for p,h in audit['bindings'].items());receipt=read(out/'receipt.json');protocol=read(out/'protocol.json');assert protocol['present_factors']==expected and protocol['rounds']==2 and audit['events']==2148;events+=audit['events'];bindings[str(out/'complete_event_audit.json')]=sha(out/'complete_event_audit.json')
    if role=='control':
     prev=Path(next(a['output'] for r in old['rows'] if r['case']==c['case'] for a in r['arms'] if a['initializer']==arm['initializer'] and a['timing_policy']==arm['timing_policy']))
     for name in ['initial.json','round0.json','round1.json','sketch.json']:assert read(out/name)==read(prev/name)
     assert [r['events'] for r in receipt['rounds']]==[r['events'] for r in read(prev/'receipt.json')['rounds']]
    rows.append({'case':c['case'],'initializer':arm['initializer'],'timing_policy':arm['timing_policy'],'role':role,'overflow_final':read(out/'sketch.json')['overflow_units'],'events':audit['events']})
  for init in ['raw_min','native_retained']:
   for key in ['control_output','candidate_output']:
    a,b=[Path(x[key]) for x in arms if x['initializer']==init];assert read(a/'round0.json')==read(b/'round0.json');assert read(a/'receipt.json')['rounds'][0]['events']==read(b/'receipt.json')['rounds'][0]['events'];assert read(a/'timing_round0.json')['criticalities']==read(b/'timing_round0.json')['criticalities']
 assert len(rows)==72 and events==154656
 counts={policy:sum(r['pass_case_gate'] for r in metrics['rows'] if r['timing_policy']==policy) for policy in ['warm_timing_frozen','warm_timing_round_updated']}
 (D/'terminal_review_v1.json').write_text(json.dumps({'status':'ALL72_FACTOR_ARMS154656_EVENTS_EXACT_CONTROLS_AND_ROUND0_PARITY_VERIFIED','rows':rows,'events':events,'quality_case_passes':counts,'candidate_promoted':False,'bindings':bindings,'scope':'Only present-factor schedule changed, full controls and price/event/timing audits; partial quality or overflow effects do not establish native equivalence/full paid gain/unseen evidence.'},indent=2)+'\n');print(counts)
if __name__=='__main__':main()
