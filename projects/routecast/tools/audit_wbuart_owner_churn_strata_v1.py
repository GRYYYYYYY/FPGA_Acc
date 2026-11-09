"""Input-frozen owner-change strata then binary occupancy churn/error diagnosis."""
import json
from pathlib import Path
from collections import Counter
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_owner_churn_strata_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_owner_delta_features_v1_2026-10-20/verification.json';proof=source.parent/'independent_verification_v1.json';assert all(sha(p)==h for p,h in read(proof)['bindings'].items());features=read(source)['rows'];bindings={str(p):sha(p) for p in [source,proof,Path(__file__)]};frozen=[]
 for r in features:
  groups=[]
  for q in read(r['owner_context']):
   raw=q['raw_owner_context'];category='previously_unoccupied' if raw[0]==0 else 'occupied_owner_endpoint_changed' if raw[6] else 'occupied_owner_endpoint_unchanged';assert raw[0]>0 or raw==[0]*7;groups.append({'RR':q['RR'],'category':category,'source_bit':int(raw[0]>0)})
  p=D/(r['case'].replace('/','_')+'_input_strata.json');p.write_text(json.dumps(groups,separators=(',',':'))+'\n');frozen.append({'case':r['case'],'strata':str(p)});bindings[str(p)]=sha(p)
 fp=D/'strata_frozen.json';fp.write_text(json.dumps({'status':'ALL9_SOURCE_ONLY_OWNER_STRATA_FROZEN','rows':frozen,'target_labels_read':False,'bindings':bindings},indent=2)+'\n');workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons'];predictions_path=E/'wbuart_owner_delta_cart_half_v1_2026-10-20/predictions_frozen.json';predictions=read(predictions_path)['rows'];rows=[];bindings={str(fp):sha(fp),str(predictions_path):sha(predictions_path),str(Path(__file__)):sha(__file__)}
 for item in frozen:
  case=item['case'];spec=Path(next(r['specification'] for r in workflow if r['case']==case));s=read(spec);target_path=Path(s['label_physical_audit']);truth={int(n):c for n,c in read(target_path)['node_occupancy'].items()};old={int(n):c for n,c in read(s['source_frame'])['ledger'].items()};models={}
  for mode in ['main','control31']:
   r=next(r for r in predictions if r['case']==case and r['mode']==mode);models[mode]=dict(zip(read(r['resource_ids']),read(r['point_counts'])));bindings[r['point_counts']]=sha(r['point_counts'])
  stats={name:dict(resources=0,source_bit_errors=0,new_activation=0,vacated_old_resource=0,target_occupied=0,owner38_half_errors=0,control31_half_errors=0) for name in ['previously_unoccupied','occupied_owner_endpoint_changed','occupied_owner_endpoint_unchanged']}
  for q in read(item['strata']):
   n=q['RR'];a=q['source_bit'];b=truth.get(n,0);assert old.get(n,0)==a and b in [0,1];stat=stats[q['category']];stat['resources']+=1;stat['source_bit_errors']+=a!=b;stat['new_activation']+=a==0 and b==1;stat['vacated_old_resource']+=a==1 and b==0;stat['target_occupied']+=b;stat['owner38_half_errors']+=models['main'][n]!=b;stat['control31_half_errors']+=models['control31'][n]!=b
  total=sum(v['source_bit_errors'] for v in stats.values());outside=stats['previously_unoccupied']['source_bit_errors']+stats['occupied_owner_endpoint_unchanged']['source_bit_errors'];rows.append({'case':case,'strata':stats,'source_bit_errors':total,'source_bit_errors_outside_endpoint_changed_old_owner':outside,'outside_changed_owner_fraction':outside/total if total else None});bindings[str(spec)]=sha(spec);bindings[str(target_path)]=sha(target_path);bindings[s['source_frame']]=sha(s['source_frame']);print('OWNER_CHURN_STRATA',case,total,outside,flush=True)
 out=D/'verification.json';out.write_text(json.dumps({'status':'ALL9_OWNER_STRATIFIED_BINARY_CHURN_AND_FIXED_MODEL_ERRORS_AUDITED','rows':rows,'bindings':bindings,'scope':'Posthoc target binary occupancy changes only, not target NET ownership turnover or causality proof. Clean old-owner endpoints may still reroute globally. Frozen source strata, no new predictor/fitting/metric changes; all cases retained.'},indent=2)+'\n')
if __name__=='__main__':main()
