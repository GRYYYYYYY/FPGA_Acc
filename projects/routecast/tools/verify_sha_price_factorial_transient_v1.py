"""Independent all-iteration capacity-excess classification from raw native/model ledgers."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_price_factorial_ablation_v2_2026-10-10';p=D/'transient_comparison.json';v=json.loads(p.read_text());assert v['independent_histogram_checks']==576 and all(sha(q)==h for q,h in v['bindings'].items());bindings={str(p):sha(p),str(Path(__file__)):sha(Path(__file__))}
vp=R/'experiments/sha1_frozen_hotspots_v2_2026-10-10/sha1/comparison_vectors.json';assert sha(vp)==v['bindings'][str(vp)];nodes=[x['node'] for x in json.loads(vp.read_text())['channels']];assert len(nodes)==len(set(nodes))==28188
models={}
for mode in ['both','no_span','no_overuse','neither']:
 for method,filename,field in [('initial','initial.json','ledger'),('round0','round0.json','ledger'),('final_shared','sketch.json','ledger'),('final_independent','sketch.json','independent_connection_ledger')]:
  q=D/'original'/mode/'model'/filename;assert sha(q)==v['bindings'][str(q)];models[mode+'/'+method]=json.loads(q.read_text())[field]
checked=0
assert [row['iteration'] for row in v['rows']]==list(range(1,19))
for row in v['rows']:
 q=R/'experiments/sha1_cold_iteration_routes_v1_2026-10-10/snapshot_audits_v2'/f"iteration_{row['iteration']:03d}.json";assert sha(q)==v['bindings'][str(q)];native=json.loads(q.read_text())['node_occupancy'];assert set(row['metrics'])==set(models)
 for method,pred in models.items():
  counts=Counter((pred.get(str(n),0)>1,native.get(str(n),0)>1) for n in nodes);c=row['metrics'][method]['overuse_classification'];expected=dict(tp=counts[True,True],fp=counts[True,False],fn=counts[False,True],tn=counts[False,False]);assert all(c[k]==value for k,value in expected.items()) and sum(expected.values())==28188
  tp,fp,fn=c['tp'],c['fp'],c['fn'];assert c['precision']==(tp/(tp+fp) if tp+fp else None) and c['recall']==(tp/(tp+fn) if tp+fn else None) and c['f1']==(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None);checked+=1
assert checked==288 and all(sha(q)==h for q,h in bindings.items());(D/'transient_independent_verification.json').write_text(json.dumps(dict(bindings=bindings,all18_iterations_all16_representations_full288_confusion_matrices_pass=True,numeric_histogram_checks_authenticated=576,scope='Capacity-excess classification exact; not routefailure labels or unseen/prospective accuracy.'),indent=2)+'\n');print('ALL288 TRANSIENT CONFUSION MATRICES PASS')
