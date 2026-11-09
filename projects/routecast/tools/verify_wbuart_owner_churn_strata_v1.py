"""Independently derive dirty owner NETs from original CID endpoints, then churn."""
import json
from pathlib import Path
from collections import Counter
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_owner_churn_strata_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'verification.json';v=read(p);assert len(v['rows'])==9 and all(sha(path)==h for path,h in v['bindings'].items());frozen=read(D/'strata_frozen.json');assert not frozen['target_labels_read'] and all(sha(path)==h for path,h in frozen['bindings'].items());features=read(E/'wbuart_owner_delta_features_v1_2026-10-20/verification.json')['rows'];workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons'];predictions=read(E/'wbuart_owner_delta_cart_half_v1_2026-10-20/predictions_frozen.json')['rows'];verified=[]
 for row in v['rows']:
  case=row['case'];f=next(r for r in features if r['case']==case);old={q['connection_id']:q for q in read(f['source_frame'])['records']};new={q['connection_id']:q for q in map(json.loads,Path(f['target_incidence']).read_text().splitlines())};dirty={q['net_id'] for cid,q in old.items() if (q['source'],q['sink'])!=(new[cid]['source'],new[cid]['sink'])};index={q['RR']:q for q in map(json.loads,Path(f['source_index']).read_text().splitlines())};strata=read(next(r['strata'] for r in frozen['rows'] if r['case']==case));spec=read(next(r['specification'] for r in workflow if r['case']==case));truth={int(n):c for n,c in read(spec['label_physical_audit'])['node_occupancy'].items()};model={}
  for mode in ['main','control31']:
   q=next(q for q in predictions if q['case']==case and q['mode']==mode);model[mode]=dict(zip(read(q['resource_ids']),read(q['point_counts'])))
  sums={k:Counter() for k in row['strata']}
  for item in strata:
   n=item['RR'];owner=index[n]['NET'];category='previously_unoccupied' if owner is None else 'occupied_owner_endpoint_changed' if owner in dirty else 'occupied_owner_endpoint_unchanged';a=int(owner is not None);b=truth.get(n,0);assert item=={'RR':n,'category':category,'source_bit':a};stat=sums[category];stat.update(resources=1,source_bit_errors=int(a!=b),new_activation=int(not a and b),vacated_old_resource=int(a and not b),target_occupied=b,owner38_half_errors=int(model['main'][n]!=b),control31_half_errors=int(model['control31'][n]!=b))
  assert all(dict(value)==row['strata'][key] for key,value in sums.items());total=sum(s['source_bit_errors'] for s in sums.values());outside=total-sums['occupied_owner_endpoint_changed']['source_bit_errors'];assert total==row['source_bit_errors'] and outside==row['source_bit_errors_outside_endpoint_changed_old_owner'];verified.append({'case':case,'outside_fraction':outside/total});print('OWNER_CHURN_STRATA_VERIFIED',case,flush=True)
 out=D/'independent_verification_v1.json';out.write_text(json.dumps({'status':'ALL9_CID_DERIVED_OWNER_STRATA_AND_BINARY_CHURN_COUNTS_VERIFIED','rows':verified,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Binary occupancy changes, not final owner identities or causal attribution. No new predictor or gate change.'},indent=2)+'\n');print('ALL_OWNER_CHURN_STRATA_VERIFIED')
if __name__=='__main__':main()
