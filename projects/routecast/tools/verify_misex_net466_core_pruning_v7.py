"""Independent exact-minimum core coverage and same-attempt superset checks."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=R/'experiments/misex_net466_extra_owner_joint_v7_2026-10-07';mp=R/'experiments/misex_net466_failure_minima_v3_2026-10-07';rp=out/'receipt.json';mr=mp/'receipt.json';vp=mp/'verification.json';r=json.loads(rp.read_text());m=json.loads(mr.read_text());v=json.loads(vp.read_text());assert v['rows_verified']==len(m['rows']);bindings={**v['bindings'],str(rp):sha(rp),str(mr):sha(mr),str(vp):sha(vp),str(Path(__file__).resolve()):sha(__file__)};assert all(sha(k)==h for k,h in bindings.items());proofs={(Path(x['branch_file']).parent.name,x['net']):x for x in m['rows']};cores=prunes=0
for attempt in r['attempts']:
 branches=attempt['branches']
 for i,b in enumerate(branches):
  assert b['index']==i
  for c in b.get('ordinary_cores',[]):
   x=proofs[(f"attempt{attempt['index']}_branch{i}",c['net'])];assert x['query']==c['query'] and x['budget']==c['budget'] and x['bans']==c['bans'] and x['release']==attempt['release'];assert x['minimum_integer']==c['minimum_integer'] and not x['ordinary_budget_feasible'];cores+=1
  if b['status']=='PRUNED_ORDINARY_CORE':
   j=b['core_branch'];assert 0<=j<i;source=branches[j];cs={tuple(x) for x in b['constraints']};assert any({(c['net'],node) for node in c['bans']}<=cs for c in source.get('ordinary_cores',[]));assert b['failures']=={};prunes+=1
assert all(sha(k)==h for k,h in bindings.items());(out/'core_pruning_verification.json').write_text(json.dumps(dict(bindings=bindings,cores_verified=cores,pruned_supersets_verified=prunes,scope='Exact ordinary minima and same-release constraint-superset implications only; no unseen branch completeness.'),indent=2)+'\n');print('PASS core pruning',cores,prunes)
