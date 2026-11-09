"""Prespecified cumulative-prefix support and future candidate novelty attribution."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from verify_prince_ready_owner_forecast_v1 import ready_inverse,final_inverse
from evaluate_prince_competitive_support_v1 import score
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_cumulative_prefix_novelty_v1_2026-10-20';S=E/'prince_competitive_frontier_trial_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def category(last,t):return 'ready' if last==t else 'previous_only' if last==t-1 else 'earlier_only' if last else 'never_seen'
def main():
 frozen=load(D/'frozen_inputs.json');assert all(sha(p)==h for p,h in frozen['bindings'].items());priorp=E/'prince_competitive_support_v1_2026-10-20/verification.json';prior={r['case']:r for r in load(priorp)['rows']};bindings={str(p):sha(p) for p in [D/'frozen_inputs.json',priorp,Path(__file__),R/'tools/evaluate_prince_competitive_support_v1.py']};rows=[]
 for row in frozen['rows']:
  c=row['case']
  if row['status']!='CUMULATIVE_INPUTS_FROZEN_NO_LABELS':rows.append(dict(case=c,status=row['status']));continue
  t=row['ready_iteration'];src=S/c/'capture';op=src/'owners'/f'owners_{t}.bin';lp=src/'queries.tsv.ledger.bin';ready=ready_inverse(op);terminal=final_inverse(lp);new={(net,n) for n,ns in terminal.items() for net in ns if net not in ready.get(n,set())};arrivals={n for net,n in new if not ready.get(n)};records=list(map(json.loads,Path(row['path']).open()));assert len(records)==row['pairs'];history={};nodehistory={name:{} for name in ['preheap','pop']};selected={mode:{name:set() for name in ['preheap','pop']} for mode in ['ready','two_phase_union','entire_prefix']}
  for x in records:
   key=x['net'],x['node'];assert key not in history;history[key]=x
   for name in ['preheap','pop']:
    mask=x[name+'_phase_mask'];last=x[name+'_last'];assert 0<=mask<1<<t;assert last==(mask.bit_length() if mask else None);assert x[name+'_first']==((mask&-mask).bit_length() if mask else None);assert bool(mask)==bool(x[name+'_events'])
    if not mask:continue
    selected['entire_prefix'][name].add(key);nodehistory[name][x['node']]=max(last,nodehistory[name].get(x['node'],0))
    if mask&(1<<(t-1)):selected['ready'][name].add(key)
    if mask&(3<<(t-2)):selected['two_phase_union'][name].add(key)
  methods={mode:{name:score(s,ready,new,arrivals) for name,s in methods.items()} for mode,methods in selected.items()}
  for mode in ['ready','two_phase_union']:
   for name in ['preheap','pop']:assert methods[mode][name]==prior[c]['methods'][mode][name]
  novelty={};added={}
  for name in ['preheap','pop']:
   pairclasses=Counter();nodeclasses=Counter();first=Counter();lasts=Counter()
   for key in new:
    x=history.get(key,{});last=x.get(name+'_last');pairclasses[category(last,t)]+=1
    if last:first[x[name+'_first']]+=1;lasts[last]+=1
   for n in arrivals:nodeclasses[category(nodehistory[name].get(n),t)]+=1
   for counter,total in [(pairclasses,len(new)),(nodeclasses,len(arrivals))]:assert sum(counter.values())==total
   assert pairclasses['never_seen']==len(new)-methods['entire_prefix'][name]['true_new_final_pairs'];assert nodeclasses['never_seen']==len(arrivals)-methods['entire_prefix'][name]['true_global_arrivals']
   novelty[name]=dict(new_owner_pair_classes={k:pairclasses[k] for k in ['ready','previous_only','earlier_only','never_seen']},global_arrival_classes={k:nodeclasses[k] for k in ['ready','previous_only','earlier_only','never_seen']},first_phase_histogram=dict(sorted(first.items())),last_phase_histogram=dict(sorted(lasts.items())));added[name]=score(selected['entire_prefix'][name]-selected['two_phase_union'][name],ready,new,arrivals)
  rows.append(dict(case=c,status='CUMULATIVE_SUPPORT_AND_NOVELTY_ATTRIBUTED',new_final_owner_pairs=len(new),global_arrivals=len(arrivals),methods=methods,novelty=novelty,added_vs_two_phase=added));print('CUMULATIVE_NOVELTY',c,{name:(methods['entire_prefix'][name]['new_pair_precision'],methods['entire_prefix'][name]['new_pair_recall'],novelty[name]['new_owner_pair_classes']) for name in ['preheap','pop']},flush=True)
  for p in [op,lp]:bindings[str(p)]=sha(p)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items())
 with (D/'verification.json').open('x') as f:json.dump(dict(status='CUMULATIVE_PREFIX_NOVELTY_SCREEN_NOT_FORECAST_ADMISSION',rows=rows,bindings=bindings,full9_gate=False,scope='Candidate observation is not previous ownership,reachable path or future selection proof. All exposed development;support screen not original rank gate,native utility,fullpaid,unseen or hardware admission.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
