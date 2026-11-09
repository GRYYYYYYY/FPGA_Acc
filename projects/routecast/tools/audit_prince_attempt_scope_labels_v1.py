"""Printed-route targets, raw actual search boxes and exact margin-sign audit."""
import json,struct
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from verify_prince_ownership_ledger_v2 import owner_payload
from evaluate_prince_ready_owner_forecast_v1 import final_owners
from verify_prince_BB_conditional_demand_v1 import graph
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_attempt_scope_competition_v1_2026-10-20';S=E/'prince_search_attempt_trial_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def exact(w):return struct.unpack('<f',struct.pack('<I',w))[0].as_integer_ratio()
def main():
 frozen=load(D/'frozen_inputs.json');v=load(D/'verification.json');by={r['case']:r for r in v['rows']};hp=E/'prince_cumulative_prefix_novelty_v1_2026-10-20/frozen_inputs.json';hist={r['case']:r for r in load(hp)['rows']};rows=[];checked=target_count=0;graphs={};bindings={str(p):sha(p) for p in [D/'frozen_inputs.json',D/'verification.json',D/'independent_input_verification_v1.json',Path(__file__)]}
 for row in frozen['rows']:
  if row['status']!='ACTUAL_SCOPE_AND_MARGIN_INPUTS_FROZEN':continue
  c=row['case'];t=row['ready_iteration'];src=S/c/'capture';w=c.split('/')[0]
  if w not in graphs:graphs[w]=graph(E/'prince_native_cohort_v1_2026-10-20'/w/'source/rr_graph.xml')
  points=graphs[w];it,owners=owner_payload(src/'owners'/f'owners_{t}.bin');assert it==t;gold=final_owners(src/'output.route');rp={(net,n) for net,ns in owners.items() for n in ns};fp={(net,n) for net,ns in gold.items() for n in ns};new=fp-rp;ready_nodes={n for net,n in rp};arrivals={n for net,n in new if n not in ready_nodes};assert len(fp)==len({n for net,n in fp});seen={}
  for x in map(json.loads,Path(hist[c]['path']).open()):
   if (x['net'],x['node']) in new:seen[x['net'],x['node']]=x
  boxes={mode:defaultdict(set) for mode in ['ready','prefix']}
  with (src/'frontier.bin.attempts.bin').open('rb') as f:
   assert f.read(8)==b'RCATT001'
   while True:
    raw=f.read(256)
    if not raw:break
    a=struct.unpack('<32Q',raw)
    if a[0]!=1:continue
    assert a[1]<=t;b=tuple(x-(1<<64) if x>=1<<63 else x for x in a[10:16]);boxes['prefix'][a[2]].add(b)
    if a[1]==t:boxes['ready'][a[2]].add(b)
  scope={mode:{tag:Counter() for tag in ['preheap','pop']} for mode in boxes}
  for net,n in new:
   for mode,netboxes in boxes.items():
    bb=netboxes.get(net,set());p=points[n]
    if not bb:category='no_attempt'
    elif any(not any(p[k]<b[2*k] or p[k]>b[2*k+1] for k in range(3)) for b in bb):category='inside_some_attempt_BB'
    else:category='outside_all_attempt_BBs'
    for tag in ['preheap','pop']:
     if not seen.get((net,n),{}).get(tag+'_phase_mask'):scope[mode][tag][category]+=1
  assert {m:{tag:dict(cnt) for tag,cnt in tags.items()} for m,tags in scope.items()}==by[c]['scope_of_never_observed'];support={mode:{name:set() for name in ['all_preheap','nonpositive_margin','positive_margin','unavailable_margin']} for mode in boxes}
  for x in map(json.loads,Path(row['margins']).open()):
   mode=x['horizon'];key=x['net'],x['node'];support[mode]['all_preheap'].add(key)
   if x['normalizable_events']:
    a,b=exact(x['min_f_bits']);cnum,d=exact(x['min_sink_f_bits']);category='nonpositive_margin' if a*d<=cnum*b else 'positive_margin'
   else:category='unavailable_margin'
   support[mode][category].add(key)
  for mode,groups in support.items():
   for name,s in groups.items():
    eligible=s-rp;nodes={n for net,n in eligible if n not in ready_nodes};tp=len(eligible&new);ntp=len(nodes&arrivals);metrics=dict(new_pair_candidates=len(eligible),true_new_final_pairs=tp,new_pair_precision=tp/len(eligible) if eligible else None,new_pair_recall=tp/len(new),global_arrival_candidates=len(nodes),true_global_arrivals=ntp,global_arrival_precision=ntp/len(nodes) if nodes else None,global_arrival_recall=ntp/len(arrivals));assert metrics==by[row['case']]['margin_metrics'][mode][name];checked+=1
  target_count+=len(new);rows.append(dict(case=row['case'],new_owner_pairs=len(new)));print('ACTUAL_SCOPE_AND_MARGIN_LABELS_PASS',row['case'],len(new),flush=True)
 assert checked==48 and target_count==8119 and len(v['rows'])==9
 with (D/'independent_label_verification_v1.json').open('x') as f:json.dump(dict(status='PRINTED_TARGETS_RAW_ACTUAL_BOXES_AND48_MARGIN_SUPPORT_SUMMARIES_RECONCILED',support_summaries=checked,new_owner_pairs=target_count,rows=rows,bindings=bindings,scope='No new predictor admission. Explicit target-specific/existential-box caveats retained.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
