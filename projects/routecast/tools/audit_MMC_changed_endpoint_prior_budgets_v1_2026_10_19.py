"""All three registered placement changes: prior actual budgets vs certified new floors."""
import pathlib,json,hashlib
from collections import Counter,defaultdict
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_changed_endpoint_prior_budgets_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O.mkdir(exist_ok=False);source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';sp=source.parent/'independent_xml_verification_v1.json';sv=json.loads(sp.read_text());assert sv['all_paths_original_XML_fraction_RC_budget_singleparent_and_uniqueNET_pass'] and sv['bindings'][str(source)]==sha(source);old=json.loads(source.read_text());records={q['connection_id']:q for q in old['records']};bindings={str(p):sha(p) for p in [source,sp,pathlib.Path(__file__).resolve()]};results=[]
 for i in [1,2,3]:
  case=f'episode_{i:02d}';I=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'/case;D=R/'experiments/mmc_prospective_swap_initializers_v1_2026-10-19'/case;ep=I/'demand/endpoints.json';meta=json.loads(ep.read_text());fresh=D/'fresh_raw/initial.json';proof=D/'fresh_raw/independent_xml_verification_v2.json';pv=json.loads(proof.read_text());assert pv['all_paths_original_XML_fraction_RC_budget_singleparent_and_uniqueNET_pass'] and pv['bindings'][str(fresh)]==sha(fresh);frame=json.loads(fresh.read_text());floors={q['connection_id']:q for q in frame['records']};new={q['connection_id']:q for q in meta['connections']};assert set(new)==set(records)==set(floors);dirty=set();changed=[];reused=0;types=Counter()
  for cid,q in new.items():
   before=records[cid];assert before['net_id']==q['net_id'];different=any(before[k]!=q[k] for k in ['source','sink'])
   if not different:reused+=1;continue
   dirty.add(q['net_id']);f=floors[cid];assert type(f['floor_integer']) is int and all(f[k]==q[k] for k in ['source','sink','net_id']);floor=f['floor_integer'];budget=before['answer']['delay'];kind=('source' if before['source']!=q['source'] else '')+('sink' if before['sink']!=q['sink'] else '');types[kind]+=1;changed.append(dict(connection_id=cid,net_id=q['net_id'],old_source=before['source'],old_sink=before['sink'],new_source=q['source'],new_sink=q['sink'],new_certified_RC_floor=floor,prior_actual_RC_budget=budget,floor_exceeds_prior_actual_budget=floor>budget,minimum_necessary_budget_increase=max(0,floor-budget)))
  # Endpoint-equal siblings in dirty NETs are not automatically safe to freeze
  # during coupled search; old native shared-tree capacity remains an obligation.
  dirty_connections=sum(q['net_id'] in dirty for q in new.values());impossible=[q for q in changed if q['floor_exceeds_prior_actual_budget']];row=dict(case=case,total_connections=len(new),endpoint_changed_connections=len(changed),endpoint_unchanged_connections=reused,affected_NETs=len(dirty),all_connections_in_affected_NETs=dirty_connections,unchanged_siblings_in_affected_NETs=dirty_connections-len(changed),change_types=dict(types),changed_connections_with_impossible_prior_actual_budget=len(impossible),minimum_necessary_sum_RC_budget_increase_units_1e18=sum(q['minimum_necessary_budget_increase'] for q in impossible),rows=changed)
  (O/f'{case}.json').write_text(json.dumps(row,indent=2)+'\n');results.append({k:v for k,v in row.items() if k!='rows'});print(results[-1],flush=True)
  for p in [ep,fresh,proof,D/'initial_independent_verification_v1.json']:bindings[str(p)]=sha(p)
 (O/'results.json').write_text(json.dumps(dict(status='ALL3_REGISTERED_ENDPOINT_CHANGE_AND_PRIOR_ACTUAL_BUDGET_CENSUS_COMPLETE',cases=results,bindings=bindings,scope='Known exposed MMC development cohorts. Only changed endpoint floors have admitted full-graph certificates from existing independent XML audits. Prior actual RC budgets may be infeasible after movement; floor<=budget is only a necessary condition, not joint capacity feasibility. Endpoint equality alone does not freeze dirty-NET parent sharing. No target native labels used by this audit, new prediction quality or speedup claim.'),indent=2)+'\n')
if __name__=='__main__':main()
