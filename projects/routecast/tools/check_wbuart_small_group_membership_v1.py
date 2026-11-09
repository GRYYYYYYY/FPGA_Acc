"""Exact physical-tree membership for diagnostic small donor groups."""
import json,hashlib
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_small_group_membership_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def signature(records):return tuple(sorted((q['connection_id'],q['source'],q['sink'],tuple(q['answer']['physical_edge_ids'])) for q in records))
def main():
 D.mkdir(exist_ok=False);C=E/'wbuart_donor_closure_diagnosis_v1_2026-10-20';P=E/'wbuart_fixed_horizon_trial_v1_2026-10-20/manifest.json';bindings={str(p):sha(p) for p in [Path(__file__),C/'verification.json',C/'independent_verification_v1.json',P]};rows=[]
 for c in read(C/'verification.json')['rows']:
  groups=[g for g in read(c['payload'])['groups'] if g['size']<=2 and g['all_target_paths_budget_compatible']];needed={n for g in groups for n in g['NETs']};refs={r['net_id']:r for r in read(c['native_reference_payload'])};target={n:signature(refs[n]['native_records']) for n in needed};case=next(x for x in read(P)['cases'] if x['case']==c['case']);arm=next(a for a in read(Path(case['output'])/'verification.json')['arms'] if a['initializer']=='native_retained' and a['timing_policy']=='warm_timing_round_updated');out=Path(arm['output']);initial=defaultdict(list)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  matches={n:[] for n in needed};counts=defaultdict(int)
  def offer(n,records,where):
   if n not in needed:return
   counts[n]+=1
   if signature(records)==target[n]:matches[n].append(where)
  for n,records in initial.items():offer(n,records,{'stage':'initial'})
  receipt=read(out/'receipt.json')
  for rnd in receipt['rounds']:
   for i,e in enumerate(rnd['events']):
    for k in ['records','rejected_records']:
     if k in e:offer(e['net_id'],e[k],{'round':rnd['round_index'],'index':i,'key':k,'status':e['status']})
  payload={'NETs':[{'net_id':n,'candidate_observations':counts[n],'exact_native_tree_matches':matches[n],'target_signature_sha256':hashlib.sha256(repr(target[n]).encode()).hexdigest()} for n in sorted(needed)],'groups':[{'group_id':g['group_id'],'NETs':g['NETs'],'all_exact_native_trees_available':all(matches[n] for n in g['NETs']),'missing_NETs':[n for n in g['NETs'] if not matches[n]],'joint_overflow_delta':g['joint_overflow_delta']} for g in groups]};folder=D/c['case'];folder.mkdir(parents=True);p=folder/'membership.json';p.write_text(json.dumps(payload)+'\n');summary={'case':c['case'],'payload':str(p),'groups':len(groups),'groups_with_all_exact_trees':sum(g['all_exact_native_trees_available'] for g in payload['groups']),'needed_NETs':len(needed),'NETs_with_exact_tree':sum(bool(matches[n]) for n in needed),'model_output':str(out),'donor_payload':c['payload'],'native_reference_payload':c['native_reference_payload']};rows.append(summary);print(summary['case'],summary['groups'],summary['groups_with_all_exact_trees'],summary['needed_NETs'],summary['NETs_with_exact_tree'],flush=True)
  for p in [p,Path(c['payload']),Path(c['native_reference_payload']),out/'receipt.json',out/'initial.json',Path(arm['audit'])]:bindings[str(p)]=sha(p)
 assert len(rows)==9
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_SMALL_BUDGET_COMPATIBLE_GROUPS_EXACT_PHYSICAL_MEMBERSHIP_CHECKED','rows':rows,'bindings':bindings,'scope':'Complete original CID/source/sink/physical-edge-sequence membership, not CHANNEL support equality. Native target groups are label-directed diagnoses. Available perNET candidates may originate different round snapshots; no simultaneous admission, joint objective, executable group policy or quality gain claim.'},indent=2)+'\n')
if __name__=='__main__':main()
