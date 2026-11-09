"""Posthoc original topK set accounting and frozen training support, all3 cases."""
import json,array
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def ar(p,t):
 a=array.array(t);a.frombytes(p.read_bytes());return a

def main():
 out=R/'experiments/mmc_owner_frequency_topK_diagnosis_v1_2026-10-19';out.mkdir(exist_ok=False);cp=R/'experiments/mmc_resource_context_v1_2026-10-19/CHANNEL_ids.u32';ids=ar(cp,'I');assert len(ids)==258720;qp=R/'experiments/mmc_owner_frequency_quality_v1_2026-10-19/results.json';quality=read(qp);fqp=R/'experiments/mmc_resource_probability_quality_v1_2026-10-19/results.json';fq=read(fqp);rows=[];bindings={str(p):sha(p) for p in [cp,qp,fqp,Path(__file__).resolve()]};k=12936
 for row in quality['rows']:
  case=row['case'];protocol=R/f'experiments/mmc_all_NET_feedback_quality_v1_2026-10-18/{case}/protocol.json';p=read(protocol);tp=Path(p['labels']['cold']);truth={int(n):v for n,v in read(tp)['node_occupancy'].items()};assert all(truth.get(n,0) in (0,1) for n in ids)
  prevp=Path(p['predictions']['previous_native']);prev=read(prevp);previous={int(n):v for n,v in prev['ledger'].items()};ownerp=R/f'experiments/mmc_owner_frequency_development_v1_2026-10-19/{case}/ledger.json';frozenp=R/f'experiments/mmc_resource_probability_development_v1_2026-10-19/{case}/history_A_B_prefix_direction_segment/ledger.json';owner={int(n):v for n,v in read(ownerp).items()};frozen={int(n):v for n,v in read(frozenp).items()};mp=ownerp.with_name('model.json');m=read(mp);ctx=R/f'experiments/mmc_resource_owner_context_v1_2026-10-19/{case}.u16';codes=dict(zip(ids,ar(ctx,'H')))
  top=lambda d:set(sorted(ids,key=lambda n:(-d.get(n,0),n))[:k]);tt=top(truth);ot=top(owner);ft=top(frozen);pt=top(previous);hits={name:len(s&tt) for name,s in [('owner',ot),('frozen216',ft),('previous_native',pt)]};assert abs(hits['owner']/k-row['metrics']['concrete']['precision_at_k'])<1e-15;assert abs(hits['previous_native']/k-next(c['reference'] for c in row['comparisons']['previous_native']['checks'] if (c['scope'],c['metric'])==('concrete','precision_at_k')))<1e-15
  fr=next(r for r in fq['rows'] if r['case']==case and r['arm']==fq['primary_arm']);assert abs(hits['frozen216']/k-fr['metrics']['concrete']['precision_at_k'])<1e-15
  groups={}
  for name,ns in [('owner_only_vs_frozen',ot-ft),('frozen_only_vs_owner',ft-ot),('baseline_hits_lost_by_both',(pt&tt)-ot-ft),('baseline_hits_lost_only_by_owner',((pt&tt)-ot)&ft),('baseline_hits_lost_only_by_frozen',((pt&tt)-ft)&ot),('owner_hits_added_vs_baseline',(ot&tt)-pt),('owner_nonhits_added_vs_baseline',(ot-tt)-pt)]:
   hist=Counter(codes[n] for n in ns);assert sum(hist.values())==len(ns);groups[name]=dict(resources=len(ns),truth_topK_hits=len(ns&tt),truth_occupied=sum(truth.get(n,0) for n in ns),unseen_training_category_resources=sum(v for c,v in hist.items() if m['counts'][c]==0),minimum_training_category_count=min((m['counts'][c] for c in hist),default=None),categories=[dict(category=c,evaluation_resources=count,training_resources=m['counts'][c],training_occupied=m['occupied'][c],frozen_probability_int=m['probability_int'][c]) for c,count in sorted(hist.items())])
  assert hits['owner']-hits['frozen216']==len((ot-ft)&tt)-len((ft-ot)&tt)
  # Independent scanning by original ID order checks exact tie-boundary sets.
  for d,s in [(owner,ot),(frozen,ft),(previous,pt)]:
   boundary=min(d.get(n,0) for n in s);above={n for n in ids if d.get(n,0)>boundary};ties=[n for n in ids if d.get(n,0)==boundary];assert s==above|set(ties[:k-len(above)])
  rows.append(dict(case=case,hits=hits,owner_frozen_topK_symmetric_difference=len(ot^ft),groups=groups));bindings.update({str(p):sha(p) for p in [protocol,tp,prevp,ownerp,frozenp,mp,ctx]});print(case,hits,'owner/frozen changed topK',len(ot^ft),'lostbyboth',groups['baseline_hits_lost_by_both']['resources'],flush=True)
 with (out/'results.json').open('x') as f:json.dump(dict(status='ALL3_ORIGINAL_TOPK_MEMBERSHIPS_SET_ACCOUNTING_AND_FROZEN_CATEGORY_SUPPORT_VERIFIED',rows=rows,bindings=bindings,scope='Posthoc diagnostics, original score/tie/K unchanged. Counts are descriptive; no train-support threshold or probability tuning. Binary truth topK remains original ascending-ID tie rule, not all occupied resources.'),f,indent=2)
if __name__=='__main__':main()
