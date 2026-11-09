"""Rejection and allocation-failure isolation for projected path ownership."""
import hashlib,json
from pathlib import Path
import incremental_NET_group_ownership_v1 as core

def main():
 out=Path('experiments/incremental_NET_group_rejections_v1_2026-10-18');out.mkdir(exist_ok=False)
 a=dict(connection_id=0,net_id=1,nodes=[1]);b=dict(a,nodes=[2]);c=core.Cache('g',{0:[1,2]},[a]);passed=[]
 def reject(name,fn,expected=ValueError):
  before=c.snapshot()
  try:fn()
  except expected:pass
  else:raise AssertionError(name)
  assert c.snapshot()==before;passed.append(name)
 def prepare(old,new):return c.prepare('g',0,[dict(old=old,new=new)])
 reject('graph',lambda:c.prepare('bad',0,[dict(old=a,new=b)]))
 reject('generation',lambda:c.prepare('g',1,[dict(old=a,new=b)]))
 reject('bool_generation',lambda:c.prepare('g',False,[dict(old=a,new=b)]))
 reject('empty',lambda:c.prepare('g',0,[]))
 reject('noop_set',lambda:prepare(a,dict(a,nodes=[1,1])))
 reject('stale_old',lambda:prepare(dict(a,nodes=[]),b))
 reject('CID_change',lambda:prepare(a,dict(b,connection_id=5)))
 reject('NET_change',lambda:prepare(a,dict(b,net_id=5)))
 reject('unknown_node',lambda:prepare(a,dict(b,nodes=[99])))
 reject('bool_node',lambda:prepare(a,dict(b,nodes=[True])))
 reject('duplicate_CID',lambda:c.prepare('g',0,[dict(old=a,new=b)]*2))
 reject('schema',lambda:prepare(a,dict(b,extra=1)))
 saved=core.patched
 def fail(*args):raise MemoryError('injected COW allocation failure')
 core.patched=fail;reject('allocation_failure',lambda:prepare(a,b),MemoryError);core.patched=saved
 ticket=prepare(a,b);c.commit(ticket)
 assert c.snapshot()['nets'][1][1]=={0:1};passed.append('same_group_node_swap_preserves_k')
 bindings={str(Path(p).resolve()):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in [__file__,'tools/incremental_NET_group_ownership_v1.py','tools/incremental_IPIN_feature_cache_v1.py','tools/net_group_collision_risk_v1.py']}
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',fixtures=passed,bindings=bindings,scope='Projection-accounting interface only, no physical path legality'),f,indent=2)
 print(json.dumps(passed))
if __name__=='__main__':main()
