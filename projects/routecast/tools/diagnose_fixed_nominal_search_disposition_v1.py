"""All12 audited runs: classify actual NET searches and replacements without reruns."""
import json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';I=E/'prospective_external_family_fixed_nominal_NET_error_v1_2026-10-19';D=E/'prospective_external_family_fixed_nominal_search_disposition_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def paths(rows):return {q['connection_id']:q['answer']['physical_edge_ids'] for q in rows}
def main():
 decision=read(I/'research_decision_v1.json');assert all(sha(p)==h for p,h in decision['bindings'].items());D.mkdir(exist_ok=False);bindings={str(I/'research_decision_v1.json'):sha(I/'research_decision_v1.json'),str(Path(__file__).resolve()):sha(__file__)};results=[]
 for c in read(A/'protocol.json')['cases']:
  case=c['case'];metadata={n['net_id']:n for n in read(I/case/'per_NET.json')};cohort={n for n,row in metadata.items() if row['category']=='endpoint_unchanged' and row['target_changed_from_source']};case_results=[]
  for init in ('raw_min','native_retained'):
   for policy in ('warm_timing_frozen','warm_timing_round_updated'):
    out=A/case/init/policy;receipt=read(out/'receipt.json');audit=read(out/'complete_event_audit.json');assert audit['complete_round_timing_original_XML_recurrence_component_assembly_and_setup_pass'];state={};netrows=[]
    for rec in read(out/'initial.json')['records']:state.setdefault(rec['net_id'],[]).append(rec)
    traces={n:[] for n in state}
    for ri,rr in enumerate(receipt['rounds']):
     for event in rr['events']:
      n=event['net_id'];old=state[n];oldpaths=paths(old);new=event.get('records');rejected=event.get('rejected_records');searched=event['primary_search_connection_ids'];retained=event['retained_connection_ids'];assert len(searched)==event['primary_search_calls'];assert set(searched).isdisjoint(retained)
      changed=new is not None and paths(new)!=oldpaths
      outcome=('committed_changed' if changed else 'committed_same' if new is not None else event['status'].lower())
      traces[n].append(dict(round_index=ri,search_calls=len(searched),retained_CIDs=len(retained),connections=len(old),outcome=outcome,rejected_candidate_changed=(paths(rejected)!=oldpaths if rejected else None),fallback_status=event.get('fallback',{}).get('status')))
      if new is not None:state[n]=new
     expected=paths(read(Path(rr['state_file']))['records']);assert paths([q for rows in state.values() for q in rows])==expected
    final=read(out/'sketch.json');assert paths(final['records'])==paths([q for rows in state.values() for q in rows]);hist=Counter();eventhist=Counter();searchhist=Counter()
    for n in sorted(cohort):
     row=metadata[n];model=init+'/'+policy;unchanged=not row['models'][model]['changed_from_source'];t=traces[n];assert len(t)==2;search_calls=sum(x['search_calls'] for x in t);outcomes={x['outcome'] for x in t}
     if not unchanged:category='final_changed'
     elif search_calls==0:category='unchanged_no_primary_search'
     elif 'committed_changed' in outcomes:category='unchanged_after_intermediate_change'
     elif any(x.startswith('retain_') for x in outcomes):category='unchanged_with_rejection'
     else:category='unchanged_searched_committed_same'
     hist[category]+=1;searchhist['primary_calls']+=search_calls
     for x in t:eventhist[x['outcome']]+=1
     netrows.append(dict(net_id=n,category=category,final_changed=not unchanged,traces=t))
    dest=D/case/init/policy;dest.mkdir(parents=True);payload=dest/'NET_dispositions.json';payload.write_text(json.dumps(netrows)+'\n');bindings[str(payload)]=sha(payload)
    for p in [out/'receipt.json',out/'complete_event_audit.json',out/'initial.json',out/'round0.json',out/'round1.json',out/'sketch.json',I/case/'per_NET.json']:bindings[str(p)]=sha(p)
    result=dict(initializer=init,policy=policy,cohort_NETs=len(cohort),NET_categories=dict(hist),round_event_outcomes=dict(eventhist),search_calls=searchhist['primary_calls']);case_results.append(result)
    if init=='native_retained' and policy=='warm_timing_round_updated':print(json.dumps(dict(case=case,**result)),flush=True)
  results.append(dict(case=case,arms=case_results))
 assert all(sha(p)==h for p,h in bindings.items());(D/'diagnosis.json').write_text(json.dumps(dict(status='ALL12_AUDITED_ROUND_SEARCH_AND_REPLACEMENT_TRACES_RECONCILED',rows=results,bindings=bindings,scope='Endpoint-unchanged NETs whose cold target CHANNEL ownership differs from source. Final changed classification uses CHANNEL set, intermediate change uses physical edge paths. Rejection present does not prove causal necessity; unknown search remains unknown. No labels fed to prediction.'),indent=2)+'\n')
if __name__=='__main__':main()
