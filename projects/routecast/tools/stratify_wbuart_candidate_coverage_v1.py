"""All36 candidate coverage strata by target budget and actual search behavior."""
import json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_candidate_coverage_strata_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);C=E/'wbuart_candidate_coverage_v1_2026-10-20';B=E/'wbuart_native_target_budget_diagnosis_v1_2026-10-20';files=[Path(__file__),C/'verification.json',C/'independent_verification_v1.json',B/'verification.json',B/'independent_verification_v1.json'];bindings={str(p):sha(p) for p in files};assert read(C/'independent_verification_v1.json')['NET_pools']==38664;rows=[]
 for arm in read(C/'verification.json')['rows']:
  payload=read(arm['payload']);budgetpath=B/arm['case']/'connections.json';budget=read(budgetpath);bad=defaultdict(set);cats={}
  for q in budget:
   cats[q['net_id']]=q['category']
   if q['violation']:bad[q['net_id']].add(q['connection_id'])
  stats=defaultdict(Counter);statuses=defaultdict(Counter);receiptpath=Path(arm['output'])/'receipt.json';receipt=read(receiptpath)
  for rnd in receipt['rounds']:
   for e in rnd['events']:
    n=e['net_id'];s=stats[n];s['events']+=1;s['primary_search_calls']+=e['primary_search_calls'];s['primary_searched_connection_observations']+=len(e['primary_search_connection_ids']);s['retained_connection_observations']+=len(e['retained_connection_ids']);s['events_with_primary_search']+=e['primary_search_calls']>0;s['events_with_retained_pins']+=bool(e['retained_connection_ids']);s['fallback_events']+='fallback' in e;s['complete_proposals']+=('records' in e or 'rejected_records' in e);s['commits']+=e['status']=='COMMITTED';statuses[n][e['status']]+=1
  output=[];strata=defaultdict(Counter)
  for q in payload:
   n=q['net_id'];s=stats[n];assert s['events']==16 and q['candidate_observations']==s['complete_proposals']+1;missing=q['minimum_stored_support_error']>0;div=q['unique_CHANNEL_supports'];behavior='no_primary_search' if s['primary_search_calls']==0 else 'searched_single_support' if div==1 else 'searched_multiple_supports';compat='native_target_path_exceeds_budget' if bad[n] else 'native_target_path_within_budget';coverage='target_support_missing' if missing else 'target_support_present';key='|'.join([coverage,compat,behavior]);a=strata[key];a['NETs']+=1;a['minimum_support_error_sum']+=q['minimum_stored_support_error'];a['selection_gap_sum']+=q['selection_gap_at16'];a['primary_search_calls']+=s['primary_search_calls'];a['fallback_events']+=s['fallback_events'];output.append({'net_id':n,'category':cats[n],'coverage':coverage,'budget_category':compat,'behavior':behavior,'unique_CHANNEL_supports':div,'native_target_budget_violating_CIDs':sorted(bad[n]),'minimum_support_error':q['minimum_stored_support_error'],'selection_gap_at16':q['selection_gap_at16'],'events':dict(s),'statuses':dict(statuses[n])})
  d=D/arm['case']/arm['initializer']/arm['timing_policy'];d.mkdir(parents=True);p=d/'NETs.json';p.write_text(json.dumps(output)+'\n');rows.append({'case':arm['case'],'initializer':arm['initializer'],'timing_policy':arm['timing_policy'],'source_pool_payload':arm['payload'],'native_budget_payload':str(budgetpath),'receipt':str(receiptpath),'payload':str(p),'strata':{k:dict(x) for k,x in strata.items()}})
  for p in [p,budgetpath,receiptpath,Path(arm['payload'])]:bindings[str(p)]=sha(p)
  print(arm['case'],arm['initializer'],arm['timing_policy'],{k:x['NETs'] for k,x in strata.items() if k.startswith('target_support_missing')},flush=True)
 assert len(rows)==36
 (D/'verification.json').write_text(json.dumps({'status':'ALL38664_NET_POOLS_STRATIFIED_BY_COVERAGE_BUDGET_AND_SEARCH','rows':rows,'bindings':bindings,'scope':'Recorded candidate coverage associations only. Native target-path budget violation does not prove target CHANNEL support impossible under budgets. Primary calls do not guarantee diverse retained/shared-tree candidates; perNET minima not global ranking/guard feasibility. No routing, tuning or gate edits.'},indent=2)+'\n')
if __name__=='__main__':main()
