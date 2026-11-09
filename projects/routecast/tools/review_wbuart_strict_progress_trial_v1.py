"""Terminal full-trial completeness, parity, neutral commit and original-gate review."""
import json,hashlib
from pathlib import Path
from fractions import Fraction
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_strict_progress_trial_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 terminal=read(D/'terminal.json');assert terminal['all_pass'] and len(terminal['rows'])==9;metric=read(D/'independent_metrics_verification_v1.json');assert metric['metric_vectors']==54 and len(metric['rows'])==18;m=read(D/'manifest.json');assert all(sha(p)==h for p,h in m['bindings'].items());rows=[];bindings={str(p):sha(p) for p in [Path(__file__),D/'terminal.json',D/'manifest.json',D/'independent_metrics_verification_v1.json']};events=0
 old=read(E/'wbuart_forecasts_v1_2026-10-20/verification.json')
 for case in m['cases']:
  proofpath=Path(case['output'])/'verification.json';caseproof=read(proofpath);bindings[str(proofpath)]=sha(proofpath)
  for arm in caseproof['arms']:
   stats={}
   for mode in ['control','strict']:
    out=Path(arm[mode+'_output']);auditpath=out/'complete_event_audit.json';audit=read(auditpath);assert all(sha(p)==h for p,h in audit['bindings'].items());bindings[str(auditpath)]=sha(auditpath);state={q['connection_id']:q for q in read(out/'initial.json')['records']};counts=Counter()
    for rnd in read(out/'receipt.json')['rounds']:
     for e in rnd['events']:
      counts['events']+=1;counts[e['status']]+=1
      if e['status']=='COMMITTED':
       new=e['records'];changed=any(q['answer']['physical_edge_ids']!=state[q['connection_id']]['answer']['physical_edge_ids'] for q in new);neutral=Fraction(e['objective_guard']['objective_delta'])==0 and e['prospective_overflow_delta']==0
       if changed:counts['changed_commits']+=1
       if changed and neutral:counts['neutral_changed_commits']+=1
       for q in new:state[q['connection_id']]=q
     assert state=={q['connection_id']:q for q in read(out/f"round{rnd['round_index']}.json")['records']}
    assert counts['events']==2148
    if mode=='strict':assert counts['neutral_changed_commits']==0
    else:
     prior=Path(next(a['output'] for r in old['rows'] if r['case']==case['case'] for a in r['arms'] if a['initializer']==arm['initializer'] and a['timing_policy']==arm['timing_policy']))
     for name in ['initial.json','round0.json','round1.json','sketch.json']:assert read(out/name)==read(prior/name)
     assert [r['events'] for r in read(out/'receipt.json')['rounds']]==[r['events'] for r in read(prior/'receipt.json')['rounds']]
    stats[mode]=dict(counts);events+=counts['events']
   rows.append({'case':case['case'],'initializer':arm['initializer'],'timing_policy':arm['timing_policy'],'counts':stats})
 assert len(rows)==36 and events==154656
 gates={p:sum(r['pass_case_gate'] for r in metric['rows'] if r['timing_policy']==p) for p in ['warm_timing_round_updated','warm_timing_frozen']}
 result={'status':'ALL72_ARMS_154656_EVENTS_CONTROL_PARITY_AND_STRICT_NO_NEUTRAL_CHANGED_COMMITS_VERIFIED','rows':rows,'events':events,'quality_case_gate_passes':gates,'candidate_promoted':False,'quality_gate_changed':False,'full_paid_time_or_native_gain_proven':False,'scope':'Development-family algorithm trial; zero neutral commits proves intended rule only, not prediction quality or unseen-family generalization.','bindings':bindings};p=D/'research_decision_v1.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(gates))
if __name__=='__main__':main()
