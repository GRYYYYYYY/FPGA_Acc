"""Match strong archived complete hard baseline to the exact new cold-label universe."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare
out=R/'experiments/resident_wire_span_hotspots_v1_2026-10-08';sp=out/'comparison.json';sv=out/'metric_verification.json';soft=json.loads(sp.read_text());v=json.loads(sv.read_text());assert v['histogram_ranks_topk_mae_and_all_complete_scope_pass'] and v['bindings'][str(sp)]==sha(sp)
parent=R/'experiments/mcnc_pending_swap_observer_native_validation_v21_2026-10-07';hp=parent/'receipt.json';hv=parent/'verification.json';hard=json.loads(hp.read_text());proof=json.loads(hv.read_text());assert proof['bindings'][str(hp)]==sha(hp);bindings={**closure([Path(__file__)]),str(sp):sha(sp),str(sv):sha(sv),str(hp):sha(hp),str(hv):sha(hv)};rows=[]
for s in soft['rows']:
 name=s['name'];h=next((r for r in hard['rows'] if r['name']==name),None)
 if h is None or h['completed']!=h['required']:
  rows.append({'name':name,'hard_complete':False,'hard_metrics':None,'reason':'no archived case' if h is None else 'incomplete original required scope','wire_metrics':s['metrics']['wire_shared']});continue
 file=parent/name/'metric_vectors.json';assert sha(file)==h['files'][str(file)]==proof['bindings'][str(file)];bindings[str(file)]=sha(file);data=json.loads(file.read_text());newfile=out/name/'comparison_vectors.json';assert sha(newfile)==soft['bindings'][str(newfile)];bindings[str(newfile)]=sha(newfile);new=json.loads(newfile.read_text());metrics={}
 for kind,key,space,k in [('channels','node','concrete',max(1,len(data['channels'])//20)),('bins','key','spatial',20)]:
  identify=lambda x:tuple(x[key]) if isinstance(x[key],list) else x[key]
  assert {identify(x):(x['capacity'],x['native']) for x in data[kind]}=={identify(x):(x['capacity'],x['native']) for x in new[kind]}
  m=compare({identify(x):x['predicted']/x['capacity'] for x in data[kind]},{identify(x):x['native']/x['capacity'] for x in data[kind]},k);assert m==h['metrics'][space];metrics[space]=m
 rows.append({'name':name,'hard_complete':True,'matched_native_and_resource_universe':True,'hard_metrics':metrics,'wire_metrics':s['metrics']['wire_shared']})
assert all(sha(k)==v for k,v in bindings.items());(out/'repaired_hard_comparison.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Retrospective development comparison; incomplete or missing baseline is null, no workflow gain or heldout claim.'},indent=2)+'\n');print([(r['name'],r['hard_metrics']['spatial']['precision_at_k'] if r['hard_metrics'] else None,r['wire_metrics']['spatial']['precision_at_k']) for r in rows])
