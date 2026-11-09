"""Check whether outside-dirty newly violating branches were actually rerouted."""
import json,hashlib
from pathlib import Path
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_offdirty_path_changes_v1_2026-10-18';D.mkdir(exist_ok=False);bindings={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
t=load(R/'experiments/native_budget_transition_v1_2026-10-18/verification.json')
cases=load(R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json')['cases'];rows=[]
for row in t['rows']:
 if not row['new_outside_dirty_net']:continue
 w,i=row['width'],row['index'];c=next(c for c in cases if (c['width'],c['index'])==(w,i));old=load(c['old']);target=load(c['target'])
 root=R/f'experiments/retained_seed_session_cohort_v3_2026-10-08/w{w}_m{i}'
 forest=load(root/'forest.json');retained={q['connection_id'] for q in forest['retained']}
 paths={}
 for name,p in [('old',Path(old['inputs']['graph']['path']).with_name('design.route')),('seed',root/'seed.route'),('after',R/f'experiments/retained_seed_session_native_cohort_v3_2026-10-08/w{w}_m{i}/output.route')]:
  bindings[str(p)]=sha(p);paths[name]=physical_paths(p)
 for cid in row['new_outside_dirty_net']:
  q=next(q for q in target['connections'] if q['connection_id']==cid);name=target['net_names'][str(q['net_id'])]
  found={}
  for stage,data in paths.items():
   matches=[p for p in data.get(name,[]) if (p[0][0],p[-1][0])==(q['source'],q['sink'])]
   assert len(matches)==1,(w,i,cid,stage)
   found[stage]=matches[0]
  assert cid in retained and found['old']==found['seed'] and found['after']!=found['seed']
  rows.append(dict(width=w,index=i,connection_id=cid,retained_seed_path_identical_to_old=True,native_changed_path=True,old_nodes=len(found['old']),after_nodes=len(found['after'])))
  print(w,i,cid,'retained old path changed by native resume',flush=True)
bindings[str(Path(__file__))]=sha(__file__)
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,scope='Physical node/switch sequence comparison over four historical branches. Not independent physical validity or causal analysis. Native resume can change retained budget-safe paths outside endpoint dirty-NET closure.',decision='Post-native acceptance must audit the complete actual routed state, or a sound closure of all actual changes; placement dirty-NET-only acceptance misses these four new violations.'),f,indent=2);f.write('\n')
