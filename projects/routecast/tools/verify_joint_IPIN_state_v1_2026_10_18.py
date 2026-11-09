"""Independent full rebuild and pinned-view checks for joint publication."""
import hashlib,json,random,time
from pathlib import Path
import joint_IPIN_state_v1 as core
from verify_incremental_IPIN_cache_v1_2026_10_18 import oracle,edits

def verify(view,rows,groups):
 sizes={s:len(ns) for s,ns in groups.items()};owners,features=oracle(rows,sizes)
 snap=view.endpoint_snapshot();assert snap['connections']==rows and snap['owner_multiplicities']==owners and snap['features']==features
 for s,nodes in groups.items():
  value=tuple(float(x) for x in features[s][1:])
  assert all(view.score(n)==value for n in nodes)

def main():
 out=Path('experiments/joint_IPIN_state_verification_v1_2026-10-18');out.mkdir(exist_ok=False)
 bindings={str(Path(p).resolve()):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in [__file__,'tools/joint_IPIN_state_v1.py','tools/incremental_IPIN_feature_cache_v1.py','tools/verify_incremental_IPIN_cache_v1_2026_10_18.py']}
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,random_steps=100,seed=781,real_sequence=[1,2,3,0,3,2,1,0],scope='Serial captured-version readers and single-reference publication only; no untrusted score-patch API, threads, durability or native utility claim'),f,indent=2)
 groups={10:[1000,1001],11:[1002,1003,1004],12:[1005]};sources={100,101}
 rows=[dict(connection_id=i,net_id=i//2,source=100,sink=10+i%3) for i in range(20)]
 obj=core.Joint('g',groups,sources,rows);rng=random.Random(781);rejected=0
 def reject(fn):
  nonlocal rejected
  view=obj.view();before=view.endpoint_snapshot()
  try:fn()
  except (ValueError,MemoryError):pass
  else:raise AssertionError('expected rejection')
  assert obj.view().endpoint_snapshot()==before;verify(view,rows,groups);rejected+=1
 for step in range(100):
  target=[dict(r) for r in rows]
  i=rng.randrange(20);target[i]['sink']=10+(target[i]['sink']-9)%3
  if step%5==0:
   net=rng.randrange(10)
   for r in target:
    if r['net_id']==net:r['source']=201-r['source']
  delta=edits(rows,target);old=obj.view();ticket=obj.prepare('g',old.generation,delta);stale=obj.prepare('g',old.generation,delta)
  verify(obj.view(),rows,groups);obj.commit(ticket);verify(old,rows,groups);rows=target;verify(obj.view(),rows,groups)
  reject(lambda:obj.commit(stale));reject(lambda:obj.commit(ticket));reject(lambda:obj.commit(object()))
 # Allocation failure after endpoint scratch update cannot publish either state.
 saved=core.patched
 def fail(*args):raise MemoryError('injected score allocation failure')
 core.patched=fail
 target=[dict(r) for r in rows];target[0]['sink']=12 if rows[0]['sink']!=12 else 10
 reject(lambda:obj.prepare('g',obj.view().generation,edits(rows,target)))
 core.patched=saved
 # Explicit zero-demand deletion, duplicate NET membership, source-only update.
 tiny=[dict(connection_id=0,net_id=0,source=100,sink=10),dict(connection_id=1,net_id=0,source=100,sink=10)]
 t=core.Joint('g',groups,sources,tiny);new=[dict(r,sink=11) for r in tiny]
 r=t.commit(t.prepare('g',0,edits(tiny,new)));verify(t.view(),new,groups);assert t.view().score(1000)==(0.,0.)
 source_only=[dict(r,source=101) for r in new];r=t.commit(t.prepare('g',1,edits(new,source_only)));assert r['score_updates']==0;verify(t.view(),source_only,groups)
 gp=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/groups.json');g=json.loads(gp.read_text());groups={v['sink_RR']:v['members'] for v in g['groups'] if v['kind']=='direct_sink_IPIN'}
 sources={int(k) for k,v in g['fallback_reasons'].items() if v=='fixed_or_unsupported_type_SOURCE'}
 p=json.loads(Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/protocol.json').read_text())
 old=json.loads(Path('experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text())['previous_endpoint'];paths=[Path(old)]+[Path(v['endpoint']) for _,v in sorted(p['inputs'].items())]
 proof=json.loads(Path('experiments/incremental_IPIN_cache_verification_v1_2026-10-18/verification.json').read_text())
 for path in [gp,*paths]:assert hashlib.sha256(path.read_bytes()).hexdigest()==proof['bindings'][str(path.resolve())]
 snapshots=[sorted(json.loads(path.read_text())['connections'],key=lambda r:r['connection_id']) for path in paths]
 obj=core.Joint(g['graph_sha256'],groups,sources,snapshots[0]);current=0;results=[]
 for target in [1,2,3,0,3,2,1,0]:
  delta=edits(snapshots[current],snapshots[target]);old=obj.view()
  start=time.perf_counter_ns();receipt=obj.commit(obj.prepare(g['graph_sha256'],old.generation,delta));ms=(time.perf_counter_ns()-start)/1e6
  verify(old,snapshots[current],groups);verify(obj.view(),snapshots[target],groups)
  results.append(dict(target=target,updates=len(delta),complete_prepare_commit_ms=ms,receipt=receipt));current=target
 for path,h in bindings.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h
 bindings.update({str(path.resolve()):hashlib.sha256(path.read_bytes()).hexdigest() for path in [gp,*paths]})
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,random_steps=100,rejections=rejected,explicit_fixtures=['allocation_failure_no_publication','zero_demand_deletion','duplicate_NET','source_only_no_score_update'],real_transitions=results,scope='No complete feature prefetch or export on measured supplied-delta path; exploratory clocks only, not balanced full-flow benchmark.'),f,indent=2)
 print(json.dumps(dict(status='pass',rejections=rejected,real_transitions=results)))
if __name__=='__main__':main()
