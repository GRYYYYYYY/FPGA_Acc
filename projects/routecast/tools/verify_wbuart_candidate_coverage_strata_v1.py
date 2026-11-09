"""Independent predicate partition, native budget arithmetic and event projections."""
import json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_candidate_coverage_strata_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'verification.json';v=read(p);assert all(sha(n)==h for n,h in v['bindings'].items());rows=[]
 for arm in v['rows']:
  old={q['net_id']:q for q in read(arm['source_pool_payload'])};data={q['net_id']:q for q in read(arm['payload'])};assert set(data)==set(old) and len(data)==1074;bad=defaultdict(set)
  for q in read(arm['native_budget_payload']):
   assert q['violation']==(q['target_delay_integer']>q['budget_integer'])
   if q['target_delay_integer']>q['budget_integer']:bad[q['net_id']].add(q['connection_id'])
  events=defaultdict(list)
  for rnd in read(arm['receipt'])['rounds']:
   for e in rnd['events']:events[e['net_id']].append(e)
  bins=defaultdict(Counter)
  for n,q in data.items():
   prior=old[n];es=events[n];assert len(es)==16;calls=sum(e['primary_search_calls'] for e in es);complete=sum(bool('records' in e or 'rejected_records' in e) for e in es);fallback=sum('fallback' in e for e in es);assert q['events']['primary_search_calls']==calls and q['events']['complete_proposals']==complete and q['events']['fallback_events']==fallback;assert q['statuses']==dict(Counter(e['status'] for e in es));assert set(q['native_target_budget_violating_CIDs'])==bad[n];coverage='target_support_present' if prior['minimum_stored_support_error']==0 else 'target_support_missing';budget='native_target_path_exceeds_budget' if bad[n] else 'native_target_path_within_budget';behavior='no_primary_search' if calls==0 else 'searched_single_support' if prior['unique_CHANNEL_supports']==1 else 'searched_multiple_supports';assert (q['coverage'],q['budget_category'],q['behavior'])==(coverage,budget,behavior);key='|'.join([coverage,budget,behavior]);x=bins[key];x['NETs']+=1;x['minimum_support_error_sum']+=prior['minimum_stored_support_error'];x['selection_gap_sum']+=prior['selection_gap_at16'];x['primary_search_calls']+=calls;x['fallback_events']+=fallback
  assert {k:dict(x) for k,x in bins.items()}==arm['strata'];rows.append({'case':arm['case'],'initializer':arm['initializer'],'timing_policy':arm['timing_policy'],'NETs':1074})
 assert len(rows)==36
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL38664_COVERAGE_STRATA_PARTITIONS_BUDGET_ARITHMETIC_AND_EVENT_PROJECTIONS_VERIFIED','rows':rows,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Independent classification/partition and actual event/budget arithmetic, relies on prior separately verified physical candidate coverage minima.'},indent=2)+'\n');print('ALL38664_COVERAGE_STRATA_PARTITIONS_BUDGET_ARITHMETIC_AND_EVENT_PROJECTIONS_VERIFIED')
if __name__=='__main__':main()
