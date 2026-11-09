"""Target-free, read-only rebasing of rejected proposals onto final round ledger.

No route commits; frozen global overflow feasibility only, no objective acceptance.
"""
import json,sys,hashlib
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from zero_rc_budget_certificate_graph_v1 import load_graph
E=R/'experiments';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';D=E/'prospective_external_family_fixed_nominal_pair_exchange_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);p=read(A/'protocol.json');graph=Path(read(Path(p['cases'][0]['endpoint']))['inputs']['graph']['path']);g=load_graph(graph);caps=g['caps'];vs=g['vs'];us=g['us'];bindings={str(graph):sha(graph),str(Path(__file__).resolve()):sha(__file__),str(A/'protocol.json'):sha(A/'protocol.json')};results=[]
 (D/'protocol.json').write_text(json.dumps(dict(cases=[c['case'] for c in p['cases']],arm='native_retained/warm_timing_round_updated',policy='All NETs, target labels not read. Use only final-round rejected physical proposals with original positive overflow delta. Rebase complete candidates onto actual final state; keep only individually overflow-increasing proposals there. Enumerate all unordered pairs with at least one pressure-add versus removal interaction, exact joint fullgraph occupancy change. No commit, no budget/objective/forecast acceptance claimed.',bindings=bindings),indent=2)+'\n')
 def support(recs):
  out=set()
  for r in recs:
   u=r['source'];out.add(u)
   for e in r['answer']['physical_edge_ids']:assert us[e]==u;u=vs[e];out.add(u)
   assert u==r['sink']
  return out
 for c in p['cases']:
  case=c['case'];out=A/case/'native_retained/warm_timing_round_updated';receipt=read(out/'receipt.json');audit=read(out/'complete_event_audit.json');assert audit['complete_prospective_overflow_guard_rejected_candidate_and_unchanged_epoch_pass'];state=read(out/'round1.json');ledger={int(n):v for n,v in state['ledger'].items()};records=defaultdict(list)
  for r in state['records']:records[r['net_id']].append(r)
  proposals={};releases=defaultdict(set);original=0
  def cost(n,d):
   before=ledger.get(n,0);after=before+d;assert after>=0;return max(0,after-caps[n])-max(0,before-caps[n])
  for event in receipt['rounds'][1]['events']:
   if 'rejected_records' not in event or event['prospective_overflow_delta']<=0:continue
   original+=1;n=event['net_id'];old=support(records[n]);new=support(event['rejected_records']);change={u:1 for u in new-old};change.update({u:-1 for u in old-new});delta=sum(cost(u,d) for u,d in change.items())
   if delta<=0:continue
   proposals[n]=dict(change=change,delta=delta,added=new-old,removed=old-new)
   for u in old-new:releases[u].add(n)
  pairs=set()
  for n,q in proposals.items():
   for u in q['added']:
    if cost(u,1)>0:
     for m in releases[u]:
      if m!=n:pairs.add(tuple(sorted((m,n))))
  feasible=[];hist=Counter()
  for n,m in sorted(pairs):
   a=proposals[n];b=proposals[m];joint=dict(a['change'])
   for u,v in b['change'].items():joint[u]=joint.get(u,0)+v
   delta=sum(cost(u,v) for u,v in joint.items());hist[str(delta)]+=1
   if delta<=0:feasible.append(dict(nets=[n,m],individual_overflow_deltas=[a['delta'],b['delta']],joint_overflow_delta=delta,changes={str(u):v for u,v in joint.items() if v}))
  dest=D/case;dest.mkdir(parents=True);f=dest/'feasible_pairs.json';f.write_text(json.dumps(feasible)+'\n');row=dict(case=case,original_positive_overflow_rejections=original,rebased_positive_proposals=len(proposals),interaction_pairs=len(pairs),joint_nonincreasing_pairs=len(feasible),strictly_improving_pairs=sum(x['joint_overflow_delta']<0 for x in feasible),joint_delta_histogram=dict(hist));results.append(row);print(json.dumps(row),flush=True)
  for f in [f,out/'receipt.json',out/'complete_event_audit.json',out/'round1.json']:bindings[str(f)]=sha(f)
 assert all(sha(p)==h for p,h in bindings.items());(D/'diagnosis.json').write_text(json.dumps(dict(status='ALL3_TARGET_FREE_REBASED_PAIR_OVERFLOW_DIAGNOSTIC_COMPLETE',rows=results,bindings=bindings,scope='All pressure-release-interacting unordered pairs of selected proposals. Feasible pairs are not jointly committed or objective-accepted, not a new predictor. Longer cycles not enumerated.'),indent=2)+'\n')
if __name__=='__main__':main()
