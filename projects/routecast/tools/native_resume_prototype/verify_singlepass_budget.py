"""Verify fixed one-marking-pass behavior and identical floor/seed inputs vs unlimited parent."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_singlepass_floor_controls_2026-10-07';vf=out/'verification.json';v=json.loads(vf.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());parent=ROOT/'experiments/native_resume_indfloor_v2_controls_2026-10-07/verification.json';pv=json.loads(parent.read_text());assert all(sha(f)==h for f,h in pv['bindings'].items());rows=[];bindings={str(vf):sha(vf),str(parent):sha(parent)}
for w,i in ((16,1),(32,3)):
 for mode in ('workflow','cold'):
  base=ROOT/f'experiments/native_resume_singlepass_floor_w{w}_m{i}_{mode}_2026-10-07';old=ROOT/f'experiments/native_resume_indfloor_v2_w{w}_m{i}_{mode}_2026-10-07';log=base/'first/run.log';oldlog=old/'first/run.log'
  assert sha(base/'rr_floors.txt')==sha(old/'rr_floors.txt')
  if mode=='workflow':assert sha(base/'first_seed.route')==sha(old/'first_seed.route')
  lines=log.read_text().splitlines();previous=oldlog.read_text().splitlines();marks=[line.split() for line in lines if line.startswith('RC_FLOOR_MARKING_PASS ')];assert marks==[['RC_FLOOR_MARKING_PASS','2','1']]
  clears=[int(line.split()[1]) for line in lines if line.startswith('RC_FLOOR_BUDGET_CLEAR ')];assert clears and clears[0]==3 and clears==list(range(3,max(clears)+1))
  actions=[line.split() for line in lines if line.startswith('RC_FORCE_WHOLE_NET ')];assert all(int(x[1])==3 for x in actions);nets=[x[2] for x in actions];assert len(nets)==len(set(nets))
  initial=[line for line in lines if line.startswith('RC_FLOOR_BIND ')];oldinitial=[line for line in previous if line.startswith('RC_FLOOR_BIND ')];assert initial==oldinitial
  for f in (log,oldlog,base/'rr_floors.txt',old/'rr_floors.txt'):bindings[str(f)]=sha(f)
  rows.append(dict(width=w,index=i,mode=mode,marking_passes=marks,clear_iterations=clears,whole_net_actions=len(actions),every_net_rebuilt_at_most_once=True,parent_whole_net_actions=sum(line.startswith('RC_FORCE_WHOLE_NET ') for line in previous),floor_bytes_and_initial_bound_bindings_equal_parent=True))
result=dict(bindings=bindings,rows=rows,verifier_sha256=sha(Path(__file__)),scope='Budget resets per routing call in local route.cpp state, one marking update, subsequent flag clearing. Same floor/seed and initial bound data; parent/new full quality proof. Does not establish all marked connections were processed or better critical-object selection; no full gain claim.')
(out/'budget_verification.json').write_text(json.dumps(result,indent=2)+'\n');print([(x['width'],x['mode'],x['whole_net_actions']) for x in rows])
