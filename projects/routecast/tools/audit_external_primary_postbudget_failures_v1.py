"""Count actual weighted-path raw-budget rejection, with no feasibility inference."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];P=R/'experiments/prospective_external_family_supplementary_development_v1_2026-10-19';D=R/'experiments/prospective_external_family_primary_postbudget_audit_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);rows=[];bindings={str(Path(__file__).resolve()):sha(__file__)}
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';folder=P/'predictions'/case/'native_retained_on';proof=json.loads((folder/'complete_event_audit.json').read_text());assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and all(sha(p)==h for p,h in proof['bindings'].items());r=json.loads((folder/'receipt.json').read_text());records={x['connection_id']:x for x in json.loads((folder/'initial.json').read_text())['records']};counts=Counter();details=[]
  for rnd in r['rounds']:
   for e in rnd['events']:
    if 'primary_failed_connection_ids' in e:
     attempts={x['connection_id']:x['physical_edge_ids'] for x in e['primary_attempts']};bad=e['primary_failed_connection_ids'];with_path=[cid for cid in bad if attempts[cid] is not None];without=[cid for cid in bad if attempts[cid] is None];counts['fallback_events']+=1;counts['failed_CIDs_with_weighted_path_overbudget']+=len(with_path);counts['failed_CIDs_without_search_path']+=len(without);counts['fallback_'+e['fallback']['status']]+=1;details.append(dict(round=rnd['round_index'],NET=e['net_id'],failed_CIDs=bad,with_overbudget_path=with_path,without_path=without,fallback=e['fallback']['status']))
    if e['status']=='COMMITTED':
     for x in e['records']:records[x['connection_id']]=x
  rows.append(dict(case=case,counts=dict(counts),events=details));bindings[str(folder/'complete_event_audit.json')]=sha(folder/'complete_event_audit.json');bindings[str(folder/'receipt.json')]=sha(folder/'receipt.json');print(case,dict(counts),flush=True)
 (D/'verification.json').write_text(json.dumps(dict(status='ALL3_PRIMARY_POSTBUDGET_FAILURE_EVENTS_CLASSIFIED',rows=rows,bindings=bindings,scope='Prior independent event audit proves provided primary paths with failed raw budgets. Missing path includes remaining unsearched CIDs after first failure, not proved unreachable. Existing old wholeNET feasible fallback does not prove feasibility on current partial primary tree.'),indent=2)+'\n')
if __name__=='__main__':main()
