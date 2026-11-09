"""Compare complete old/seed/final physical paths across all12 development cases."""
import json,hashlib
from pathlib import Path
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_actual_change_closure_v1_2026-10-18';D.mkdir(exist_ok=False);bindings={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
def paths(p):
 bindings[str(p)]=sha(p);d=physical_paths(p);out={}
 for name,branches in d.items():
  for branch in branches:
   key=(name,branch[0][0],branch[-1][0]);assert key not in out;out[key]=branch
 return out
cases=load(R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json')['cases'];rows=[]
for c in cases:
 w,i=c['width'],c['index'];old=load(c['old']);target=load(c['target']);a={q['connection_id']:q for q in old['connections']};b={q['connection_id']:q for q in target['connections']}
 dirty={cid for cid in a if (a[cid]['source'],a[cid]['sink'])!=(b[cid]['source'],b[cid]['sink'])};nets={b[cid]['net_id'] for cid in dirty};closure={cid for cid in b if b[cid]['net_id'] in nets}
 root=R/f'experiments/retained_seed_session_cohort_v3_2026-10-08/w{w}_m{i}';forest=load(root/'forest.json');kept={q['connection_id'] for q in forest['retained']}
 before=paths(Path(old['inputs']['graph']['path']).with_name('design.route'));seed=paths(root/'seed.route');after=paths(R/f'experiments/retained_seed_session_native_cohort_v3_2026-10-08/w{w}_m{i}/output.route')
 changed=[];kept_changed=[]
 for cid,q in b.items():
  key=(target['net_names'][str(q['net_id'])],q['source'],q['sink']);oldq=a[cid];oldkey=(old['net_names'][str(oldq['net_id'])],oldq['source'],oldq['sink'])
  assert key in after and oldkey in before
  if before[oldkey]!=after[key]:changed.append(cid)
  if cid in kept:
   assert seed[key]==before[oldkey]
   if seed[key]!=after[key]:kept_changed.append(cid)
 assert len(after)==len(b) and len(seed)==len(kept)
 rows.append(dict(width=w,index=i,connections=len(b),placement_dirty_connections=len(dirty),placement_whole_net_closure=len(closure),final_changed_connections=len(changed),final_changed_outside_placement_dirty_net=sorted(set(changed)-closure),retained_seed_connections=len(kept),retained_seed_changed_connections=kept_changed))
 print(w,i,'actual changed',len(changed),'outside dirty NET',len(set(changed)-closure),'retained changed',len(kept_changed),flush=True)
for rel in ['tools/native_resume_prototype/build_branch_partial_v8.py','build/native_resume_branch_partial_v8_2026-10-08/source/route_net.cpp','tools/build_capacity_seed_incumbent.py','build/capacity_seed_incumbent_2026-10-06/route.cpp', 'tools/native_route_ledger_import_compact.py']:
 p=R/rel;bindings[str(p)]=sha(p)
bindings[str(Path(__file__))]=sha(__file__)
report=dict(bindings=bindings,rows=rows,source_findings={'branch_partial_resume':'First iteration skips a specific full-ripup condition when a tree exists; high-fanout hold ripup and pruning remain, later iterations do not receive that exception. No immutable per-connection budget guard.','incumbent_guard':'Requires complete legal seed and uses whole-design critical path ceiling plus native quality selection. It does not enforce original per-connection proxy budgets and cannot directly accept incomplete branch seed as legal incumbent.'},scope='Exact node/switch trace comparison, not new physical validity replay or runtime measurement; paths may remain changed within the same resource union. These12 previously exposed development targets are not unseen evaluation.',decision='Any post-native incremental acceptance must track actual changed paths/NET unions and check endpoint coverage, unique-NET occupancy, canonical pins and budgets. Retaining seed paths is not a promise they survive native routing. Do not freeze unaffected branches without explicit congestion fallback and feasibility experiments.')
with (D/'verification.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
