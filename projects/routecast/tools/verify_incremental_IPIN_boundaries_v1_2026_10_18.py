"""Named serial cache isolation, multiplicity and rejection fixtures."""
import hashlib,json
from pathlib import Path
from incremental_IPIN_feature_cache_v1 import Cache
from verify_incremental_IPIN_cache_v1_2026_10_18 import check,edits

def main():
 out=Path('experiments/incremental_IPIN_cache_boundaries_v1_2026-10-18');out.mkdir(exist_ok=False)
 sizes={10:2,11:3,12:1};sources={100,101}
 rows=[dict(connection_id=i,net_id=n,source=100,sink=s) for i,(n,s) in enumerate([(0,10),(0,10),(1,11)])]
 c=Cache('g',sizes,sources,rows);passed=[]
 def reject(name,fn):
  before=c.snapshot()
  try:fn()
  except ValueError:pass
  else:raise AssertionError(name)
  assert c.snapshot()==before;passed.append(name)
 def attempt(old,new):return c.prepare('g',c.generation,[dict(old=old,new=new)])
 for name,field,value in [('CID_change','connection_id',9),('NET_change','net_id',9),('unknown_sink','sink',999),('unknown_source','source',999),('negative_value','sink',-1),('bool_value','sink',True)]:
  new=dict(rows[0]);new[field]=value;reject(name,lambda:attempt(rows[0],new))
 new=dict(rows[0],sink=11)
 reject('duplicate_CID',lambda:c.prepare('g',0,[dict(old=rows[0],new=new)]*2))
 reject('stale_old',lambda:attempt(dict(rows[0],sink=11),dict(rows[0],sink=12)))
 reject('foreign_token',lambda:c.commit(object()))
 reject('partial_driver',lambda:attempt(rows[0],dict(rows[0],source=101)))
 reject('extra_field',lambda:attempt(rows[0],dict(new,extra=0)))
 reject('missing_field',lambda:attempt(rows[0],{k:v for k,v in new.items() if k!='sink'}))
 target=[dict(r) for r in rows];target[0]['sink']=11
 c.commit(c.prepare('g',0,edits(rows,target)));rows=target;check(c,rows,sizes)
 assert c.class_feature(10)[0]==1;passed.append('duplicate_NET_one_reference_remains')
 target=[dict(r) for r in rows];target[1]['sink']=11
 c.commit(c.prepare('g',1,edits(rows,target)));rows=target;check(c,rows,sizes)
 assert c.class_feature(10)[0]==0 and c.class_feature(11)[0]==2;passed.append('last_reference_removes_NET')
 target=[dict(r,source=101) if r['net_id']==0 else dict(r) for r in rows]
 receipt=c.commit(c.prepare('g',2,edits(rows,target)));rows=target;check(c,rows,sizes)
 assert receipt['touched_classes']==();passed.append('complete_source_only_update')
 snap=c.snapshot();snap['connections'][0]['sink']=12;snap['owner_multiplicities'][11].clear();snap['features'].clear();check(c,rows,sizes);passed.append('snapshot_isolation')
 original_sizes=dict(sizes);sizes.clear();sources.clear();check(c,rows,original_sizes);passed.append('input_context_isolation')
 bindings={str(Path(p).resolve()):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in [__file__,'tools/incremental_IPIN_feature_cache_v1.py','tools/verify_incremental_IPIN_cache_v1_2026_10_18.py']}
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',fixtures=passed,bindings=bindings,scope='Serial cache only; not placement legality or concurrent publication'),f,indent=2)
 print(json.dumps(passed))
if __name__=='__main__':main()
