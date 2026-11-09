"""Independent full-rebuild oracle for serial endpoint feature updates."""
import hashlib,json,random,time
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from incremental_IPIN_feature_cache_v1 import Cache

def oracle(rows,sizes):
 owners=defaultdict(Counter)
 for r in rows:owners[r['sink']][r['net_id']]+=1
 features={}
 for sink,m in sizes.items():
  q=len(owners.get(sink,{}))
  # Independent probability construction, including empty class.
  empty=Fraction(m-1,m)**q
  features[sink]=(q,Fraction(q,m),Fraction(q,m)-1+empty)
 return {s:dict(v) for s,v in owners.items()},features

def check(cache,rows,sizes):
 snap=cache.snapshot();owners,features=oracle(rows,sizes)
 assert snap['connections']==sorted(rows,key=lambda r:r['connection_id'])
 assert snap['owner_multiplicities']==owners
 assert snap['features']==features

def edits(a,b):
 return [dict(old=x,new=y) for x,y in zip(a,b) if x!=y]

def main():
 out=Path('experiments/incremental_IPIN_cache_verification_v1_2026-10-18');out.mkdir(exist_ok=False)
 sizes={i:1+i%7 for i in range(20)};sources={100,101};rng=random.Random(74219)
 rows=[dict(connection_id=i,net_id=i//3,source=100,sink=i%5) for i in range(90)]
 c=Cache('fixture',sizes,sources,rows);check(c,rows,sizes)
 rejected=0
 def reject(fn):
  nonlocal rejected
  before=c.snapshot()
  try:fn()
  except ValueError:pass
  else:raise AssertionError('expected rejection')
  assert c.snapshot()==before;rejected+=1
 for step in range(200):
  target=[dict(r) for r in rows]
  for i in rng.sample(range(len(rows)),rng.randint(1,15)):
   target[i]['sink']=rng.randrange(20)
  if step%7==0:
   net=rng.randrange(30)
   for r in target:
    if r['net_id']==net:r['source']=201-r['source']
  delta=edits(rows,target)
  if not delta:continue
  before=c.snapshot();ticket=c.prepare('fixture',c.generation,delta)
  assert before==c.snapshot()
  stale=c.prepare('fixture',c.generation,delta)
  # Caller changes must not alter prepared data.
  delta[0]['new']=dict(delta[0]['old'])
  c.commit(ticket);rows=target;check(c,rows,sizes)
  reject(lambda:c.commit(ticket));reject(lambda:c.commit(stale))
  reject(lambda:c.prepare('wrong',c.generation,[]))
  reject(lambda:c.prepare('fixture',c.generation-1,[]))
  reject(lambda:c.prepare('fixture',c.generation,[]))
  bad=dict(rows[0]);bad['source']=201-bad['source']
  reject(lambda:c.prepare('fixture',c.generation,[dict(old=rows[0],new=bad)]))
  reject(lambda:c.prepare('fixture',c.generation,[dict(old=rows[0],new=rows[0])]))
 group_path=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/groups.json')
 groups=json.loads(group_path.read_text());epoch=groups['graph_sha256']
 sizes={g['sink_RR']:len(g['members']) for g in groups['groups'] if g['kind']=='direct_sink_IPIN'}
 sources={int(k) for k,v in groups['fallback_reasons'].items() if v=='fixed_or_unsupported_type_SOURCE'}
 protocol=json.loads(Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/protocol.json').read_text())
 old=json.loads(Path('experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text())['previous_endpoint']
 paths=[Path(old)]+[Path(v['endpoint']) for k,v in sorted(protocol['inputs'].items())]
 proof_path=Path('experiments/mmc_IPIN_endpoint_sufficiency_v1_2026-10-18/verification.json')
 proof=json.loads(proof_path.read_text());assert proof['status']=='pass'
 bindings={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths+[group_path,proof_path,Path(__file__),Path('tools/incremental_IPIN_feature_cache_v1.py')]}
 for p in paths:
  assert bindings[str(p.resolve())]==proof['bindings'][str(p.resolve())]
 snapshots=[]
 for p in paths:
  d=json.loads(p.read_text());assert d['graph_sha256']==epoch
  snapshots.append(sorted(d['connections'],key=lambda r:r['connection_id']))
 start=time.perf_counter();c=Cache(epoch,sizes,sources,snapshots[0]);initial=time.perf_counter()-start
 check(c,snapshots[0],sizes);current=snapshots[0];results=[]
 for index in [1,2,3,0,3,2,1,0]:
  target=snapshots[index];start=time.perf_counter();delta=edits(current,target);discovery=time.perf_counter()-start
  before=c.snapshot();start=time.perf_counter();ticket=c.prepare(epoch,c.generation,delta);receipt=c.commit(ticket);elapsed=time.perf_counter()-start
  check(c,target,sizes)
  results.append(dict(target=str(paths[index]),updates=len(delta),discovery_seconds=discovery,prepare_commit_seconds=elapsed,receipt=receipt));current=target
 result=dict(status='pass',bindings=bindings,random_steps=200,rejected_updates=rejected,classes=len(sizes),connections=len(current),initial_construction_seconds=initial,transitions=results,scope='Serial feature correctness and exploratory component clocks only; not full-flow speedup or forecast promotion.')
 with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','transitions']}))
 print(json.dumps(results))
if __name__=='__main__':main()
