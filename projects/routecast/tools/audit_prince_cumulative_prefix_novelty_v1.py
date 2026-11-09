"""Independent record counters, printed labels and set-partition novelty audit."""
import json,subprocess
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from verify_prince_ownership_ledger_v2 import owner_payload
from evaluate_prince_ready_owner_forecast_v1 import final_owners
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_cumulative_prefix_novelty_v1_2026-10-20';S=E/'prince_competitive_frontier_trial_v1_2026-10-20';B=R/'build/prince_cumulative_prefix_audit_v1_2026-10-20/extract'
def load(p):return json.loads(Path(p).read_text())
def main():
 frozen=load(D/'frozen_inputs.json');v=load(D/'verification.json');by={r['case']:r for r in v['rows']};checked=records=0;rows=[];bindings={str(p):sha(p) for p in [D/'frozen_inputs.json',D/'verification.json',B,R/'tools/extract_prince_cumulative_prefix_v1.cpp',Path(__file__)]}
 for row in frozen['rows']:
  if row['status']!='CUMULATIVE_INPUTS_FROZEN_NO_LABELS':continue
  c=row['case'];t=row['ready_iteration'];src=S/c/'capture';cp=subprocess.run([str(B),str(src/'frontier.bin'),str(t)],capture_output=True,text=True);assert cp.returncode==0,cp.stderr;raw={}
  for line in cp.stdout.splitlines():
   a=list(map(int,line.split()));key=tuple(a[:2]);assert key not in raw;raw[key]=a[2:]
  saved={}
  for x in map(json.loads,Path(row['path']).open()):saved[x['net'],x['node']]=[x[k] or 0 for name in ['preheap','pop'] for k in [name+'_events',name+'_phase_mask',name+'_first',name+'_last']]
  assert raw==saved and len(raw)==row['pairs'];records+=len(raw);assert sum(a[0]+a[4] for a in raw.values())==row['events'];it,ready=owner_payload(src/'owners'/f'owners_{t}.bin');assert it==t;truth=final_owners(src/'output.route');rp={(net,n) for net,ns in ready.items() for n in ns};fp={(net,n) for net,ns in truth.items() for n in ns};new=fp-rp;rn={n for net,n in rp};arrivals={n for net,n in new if n not in rn};result=by[c];assert result['new_final_owner_pairs']==len(new) and result['global_arrivals']==len(arrivals)
  def verify(s,expected):
   nonlocal checked
   eligible=s-rp;nodes={n for net,n in eligible if n not in rn};tp=len(eligible&new);ntp=len(nodes&arrivals);actual=dict(new_pair_candidates=len(eligible),true_new_final_pairs=tp,new_pair_precision=tp/len(eligible) if eligible else None,new_pair_recall=tp/len(new),global_arrival_candidates=len(nodes),true_global_arrivals=ntp,global_arrival_precision=ntp/len(nodes) if nodes else None,global_arrival_recall=ntp/len(arrivals));assert actual==expected;checked+=1
  for name,offset in [('preheap',0),('pop',4)]:
   support=dict(ready={key for key,a in raw.items() if a[offset+1]&(1<<(t-1))},two_phase_union={key for key,a in raw.items() if a[offset+1]&(3<<(t-2))},entire_prefix={key for key,a in raw.items() if a[offset]})
   for mode,s in support.items():verify(s,result['methods'][mode][name])
   verify(support['entire_prefix']-support['two_phase_union'],result['added_vs_two_phase'][name]);expected=result['novelty'][name];r,two,allx=(support[k] for k in ['ready','two_phase_union','entire_prefix']);pairclasses=dict(ready=len(new&r),previous_only=len((new&two)-r),earlier_only=len((new&allx)-two),never_seen=len(new-allx));assert pairclasses==expected['new_owner_pair_classes'];ns=[{n for net,n in ss} for ss in [r,two,allx]];r,two,allx=ns;nodeclasses=dict(ready=len(arrivals&r),previous_only=len((arrivals&two)-r),earlier_only=len((arrivals&allx)-two),never_seen=len(arrivals-allx));assert nodeclasses==expected['global_arrival_classes']
   for field,index in [('first_phase_histogram',offset+2),('last_phase_histogram',offset+3)]:
    hist=Counter(str(raw[key][index]) for key in new if key in raw and raw[key][offset]);assert dict(hist)==expected[field]
  rows.append(dict(case=c,independent_NET_node_histories=len(raw)));print('CUMULATIVE_PREFIX_INDEPENDENT_PASS',c,len(raw),flush=True)
 assert len(rows)==6 and checked==48 and len(v['rows'])==9
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='RAW_HISTORY_AND48_SUPPORT_SUMMARIES_NOVELTY_PARTITIONS_RECONCILED',NET_node_histories=records,verified_support_summaries=checked,rows=rows,bindings=bindings,scope='Independent C++ full-record counters with explicit minima/maxima;printed final-route ownership rather than terminal binary target;set differences rather than last-seen branching. No original metric/predictor admission.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
