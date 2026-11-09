"""Replay recorded transactions; distinguish unchanged NET objective improvements."""
import json,hashlib
from pathlib import Path
from fractions import Fraction
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_unchanged_net_event_diagnosis_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);F=E/'wbuart_forecasts_v1_2026-10-20/verification.json';W=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';bindings={str(p):sha(p) for p in [Path(__file__),F,W]};rows=[];total=0
 for case in read(F)['rows']:
  spec=read(next(c['specification'] for c in read(W)['comparisons'] if c['case']==case['case']));prior={q['connection_id']:q for q in read(spec['source_frame'])['records']};queries=read(spec['endpoint'])['connections'];dirty={q['net_id'] for q in queries if (q['source'],q['sink'])!=(prior[q['connection_id']]['source'],prior[q['connection_id']]['sink'])}
  for arm in case['arms']:
   out=Path(arm['output']);audit=read(out/'complete_event_audit.json');assert all(sha(k)==h for k,h in audit['bindings'].items());bindings[str(out/'complete_event_audit.json')]=sha(out/'complete_event_audit.json');receipt=read(out/'receipt.json');state={q['connection_id']:q for q in read(out/'initial.json')['records']};rounds=[]
   for rnd in receipt['rounds']:
    counters=Counter();seen=set()
    for event in rnd['events']:
     net=event['net_id'];assert net not in seen;seen.add(net);prefix='dirty_NET' if net in dirty else 'unchanged_NET';counters[prefix+'/events']+=1;counters[prefix+'/'+event['status']]+=1
     if event['status']=='COMMITTED':
      records=event['records'];changed=sum(q['answer']['physical_edge_ids']!=state[q['connection_id']]['answer']['physical_edge_ids'] for q in records);g=event['objective_guard'];old,new,delta=(Fraction(g[k]) for k in ['old_score','candidate_score','objective_delta']);assert new-old==delta and delta<=0 and event['prospective_overflow_delta']<=0;counters[prefix+'/path_changed_CIDs']+=changed
      if changed:
       counters[prefix+'/changed_NET_commits']+=1;counters[prefix+('/changed_strict_objective_improvement' if delta<0 else '/changed_equal_objective')]+=1;counters[prefix+('/changed_overflow_reduction' if event['prospective_overflow_delta']<0 else '/changed_zero_overflow_delta')]+=1
      for q in records:state[q['connection_id']]=q
    final=read(out/f"round{rnd['round_index']}.json");assert state=={q['connection_id']:q for q in final['records']};assert len(seen)==1074;total+=len(seen);rounds.append({'round':rnd['round_index'],'counts':dict(counters)})
   rows.append({'case':case['case'],'initializer':arm['initializer'],'timing_policy':arm['timing_policy'],'rounds':rounds})
 assert len(rows)==36 and total==77328
 (D/'verification.json').write_text(json.dumps({'status':'ALL77328_RECORDED_NET_EVENTS_REPLAYED_AND_OBJECTIVE_SIGNS_CHECKED','events':total,'rows':rows,'bindings':bindings,'scope':'Replays independently audited events and exact Fraction objective sign/difference, not a new independent reconstruction of objective components. All-NET scheduling is declared, not an unexpected endpoint trigger. Local objective improvement does not establish target-label quality gain; no new routing, tuning or gate change.'},indent=2)+'\n');print('ALL77328_RECORDED_NET_EVENTS_REPLAYED_AND_OBJECTIVE_SIGNS_CHECKED')
if __name__=='__main__':main()
