"""Bound descriptive intervention counts; full quality gates remain authoritative."""
import collections,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';root=E/'mmc_all_NET_feedback_v1_2026-10-18';audit=root/'independent_audits/verification.json';v=json.loads(audit.read_text());assert v['all3_full_frames_and_all_NET_event_replays_pass'];bindings={**closure([Path(__file__)]),str(audit):sha(audit)};assert all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);rows=[]
 def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
 for case in ['case_01','case_02','case_03']:
  old=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}';warm=load(old/'native_retained/verification.json');dirty=set(warm['dirty_nets']);initial=load(root/case/'initial.json');final=load(root/case/'sketch.json');receipt=load(root/case/'receipt.json');baseline=load(old/'feedback_on/native_retained/sketch.json');baseline_receipt=load(old/'feedback_on/native_retained/receipt.json');oldproof=load(old/'feedback_audits/verification.json');assert oldproof['both_final_and_all_event_audits_pass'] and oldproof['bindings'][str(old/'feedback_on/native_retained/receipt.json')]==sha(old/'feedback_on/native_retained/receipt.json');assert baseline_receipt['files'][str(old/'feedback_on/native_retained/sketch.json')]==sha(old/'feedback_on/native_retained/sketch.json')
  seed={r['connection_id']:r for r in initial['records']};local={r['connection_id']:r for r in baseline['records']};now={r['connection_id']:r for r in final['records']};assert seed.keys()==local.keys()==now.keys();rounds=[]
  for rr in receipt['rounds']:
   strata={}
   for name,test in [('dirty',lambda n:n in dirty),('other_NETs',lambda n:n not in dirty)]:
    events=[e for e in rr['events'] if test(e['net_id'])];strata[name]=dict(scheduled=len(events),status_counts=dict(collections.Counter(e['status'] for e in events)),fallback_calls=sum('fallback' in e for e in events),primary_search_calls=sum(e['primary_search_calls'] for e in events))
   rounds.append(dict(round_index=rr['round_index'],overflow_before=rr['overflow_before'],overflow_after=rr['overflow_after'],strata=strata))
  changed=[c for c in seed if now[c]['answer']!=seed[c]['answer']];diff=[c for c in seed if now[c]['answer']!=local[c]['answer']];rows.append(dict(case=case,rounds=rounds,initial_overflow=initial['overflow_units'],original_local_final_overflow=baseline['overflow_units'],all_NET_final_overflow=final['overflow_units'],changed_CIDs_from_seed=len(changed),changed_NETs_from_seed=len({now[c]['net_id'] for c in changed}),different_CIDs_from_original_local=len(diff),different_NETs_from_original_local=len({now[c]['net_id'] for c in diff}),changed_previously_clean_NETs=len({now[c]['net_id'] for c in changed}-dirty),candidate_resident_seconds=receipt['total_paid_resident_seconds'],original_local_resident_seconds=baseline_receipt['total_paid_resident_seconds']))
 assert all(sha(p)==h for p,h in bindings.items());p=root/'intervention_summary.json'
 with p.open('x') as f:json.dump(dict(bindings=bindings,cases=rows,scope='Descriptive actual scheduled/committed interventions after independent event audit. Resident times are single unmatched observations, not complete workflow performance. Model overflow is not prediction quality or native legal route. Original cold quality gates separately required.'),f,indent=2)
 print(json.dumps(rows),flush=True)
if __name__=='__main__':main()
