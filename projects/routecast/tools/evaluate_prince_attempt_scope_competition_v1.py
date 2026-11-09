"""Actual attempt-scope attribution and prespecified margin-sign support screen."""
import json,struct
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from verify_prince_ready_owner_forecast_v1 import ready_inverse,final_inverse
from evaluate_prince_competitive_support_v1 import score
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_attempt_scope_competition_v1_2026-10-20';S=E/'prince_search_attempt_trial_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def f32(w):return struct.unpack('<f',struct.pack('<I',w))[0]
def main():
 frozen=load(D/'frozen_inputs.json');assert all(sha(p)==h for p,h in frozen['bindings'].items());hf=E/'prince_cumulative_prefix_novelty_v1_2026-10-20/frozen_inputs.json';history={r['case']:r for r in load(hf)['rows']};gf=E/'prince_ready_NET_geometry_v2_2026-10-20/frozen_inputs.json';geometry={r['case']:r for r in load(gf)['rows']};cp=E/'prince_competitive_support_v1_2026-10-20/verification.json';priorready={r['case']:r for r in load(cp)['rows']};pp=E/'prince_cumulative_prefix_novelty_v1_2026-10-20/verification.json';priorprefix={r['case']:r for r in load(pp)['rows']};bindings={str(p):sha(p) for p in [D/'frozen_inputs.json',hf,gf,cp,pp,Path(__file__)]};rows=[]
 for row in frozen['rows']:
  c=row['case']
  if row['status']!='ACTUAL_SCOPE_AND_MARGIN_INPUTS_FROZEN':rows.append(dict(case=c,status=row['status']));continue
  t=row['ready_iteration'];src=S/c/'capture';op=src/'owners'/f'owners_{t}.bin';lp=src/'queries.tsv.ledger.bin';ready=ready_inverse(op);final=final_inverse(lp);new={(net,n) for n,ns in final.items() for net in ns if net not in ready.get(n,set())};arrivals={n for net,n in new if not ready.get(n)};points={x['id']:x['drive_point'] for x in map(json.loads,Path(geometry[c]['points']).open())};boxes={mode:defaultdict(list) for mode in ['ready','prefix']}
  for x in map(json.loads,Path(row['boxes']).open()):
   assert 1<=x['phase']<=t;boxes['prefix'][x['net']].append(x['box'])
   if x['phase']==t:boxes['ready'][x['net']].append(x['box'])
  seen={}
  for x in map(json.loads,Path(history[c]['path']).open()):
   if (x['net'],x['node']) in new:seen[x['net'],x['node']]=x
  scope={mode:{tag:Counter() for tag in ['preheap','pop']} for mode in ['ready','prefix']}
  for net,n in new:
   for mode in scope:
    b=boxes[mode].get(net,[]);pt=points[n];group='no_attempt' if not b else 'inside_some_attempt_BB' if any(all(lo<=p<=hi for p,lo,hi in zip(pt,bx[::2],bx[1::2])) for bx in b) else 'outside_all_attempt_BBs'
    for tag in ['preheap','pop']:
     if not seen.get((net,n),{}).get(tag+'_events'):scope[mode][tag][group]+=1
  support={mode:{name:set() for name in ['all_preheap','nonpositive_margin','positive_margin','unavailable_margin']} for mode in ['ready','prefix']};statuses={mode:Counter() for mode in support};records=0
  for x in map(json.loads,Path(row['margins']).open()):
   records+=1;mode=x['horizon'];key=x['net'],x['node'];assert key not in support[mode]['all_preheap'];assert x['accepted_events']==sum(x[k] for k in ['normalizable_events','zero_target_events','invalid_target_events','nonfinite_candidate_events']);support[mode]['all_preheap'].add(key)
   if x['normalizable_events']:
    assert f32(x['min_sink_f_bits'])>0;group='nonpositive_margin' if f32(x['min_f_bits'])<=f32(x['min_sink_f_bits']) else 'positive_margin'
   else:group='unavailable_margin'
   support[mode][group].add(key)
   for k in ['zero_target_events','invalid_target_events','nonfinite_candidate_events']:statuses[mode][k]+=x[k]
  assert records==row['margin_records'];metrics={mode:{name:score(s,ready,new,arrivals) for name,s in groups.items()} for mode,groups in support.items()};assert metrics['ready']['all_preheap']==priorready[c]['methods']['ready']['preheap'];assert metrics['prefix']['all_preheap']==priorprefix[c]['methods']['entire_prefix']['preheap'];rows.append(dict(case=c,status='ACTUAL_SCOPE_AND_MARGIN_SCREENED',new_owner_pairs=len(new),scope_of_never_observed={mode:{tag:dict(cnt) for tag,cnt in tags.items()} for mode,tags in scope.items()},margin_metrics=metrics,normalization_exceptions={m:dict(s) for m,s in statuses.items()}));print('ATTEMPT_SCOPE_MARGIN_SCREEN',c,'scope',{m:dict(scope[m]['preheap']) for m in scope},'ready_signs',{name:(x['new_pair_precision'],x['new_pair_recall']) for name,x in metrics['ready'].items()},flush=True)
  for p in [op,lp,Path(geometry[c]['points']),Path(history[c]['path'])]:bindings[str(p)]=sha(p)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items())
 with (D/'verification.json').open('x') as f:json.dump(dict(status='ACTUAL_SCOPE_AND_MARGIN_SIGN_DIAGNOSED_NO_PREDICTOR',rows=rows,bindings=bindings,full9_gate=False,scope='Existential sameNET actual BB eligibility and margin-sign support diagnostics only. No path optimality/reachability claim,no original global quality/native/fullpaid/unseen/hardware admission.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
