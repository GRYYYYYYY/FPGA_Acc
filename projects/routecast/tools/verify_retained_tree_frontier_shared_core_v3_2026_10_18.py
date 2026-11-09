"""Independent full reconstruction over remove/restore/replace/root-change cycles."""
import collections,copy,json,random,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from retained_tree_frontier_state_v3 import Cache as SharedCache,GraphContext
def Cache(epoch,geo,records,checker):return SharedCache(GraphContext(epoch,geo,checker),records)

def main():
 out=R/'experiments/retained_tree_frontier_shared_core_v3_2026-10-18';out.mkdir(exist_ok=False);checks=commits=0;rejected=collections.Counter()
 def reject(name,fn):
  try:fn()
  except ValueError:rejected[name]+=1
  else:raise AssertionError(name)
 def verify(view,expected,geo):
  nonlocal checks
  snap=view.snapshot();assert snap['queries']==expected;group=collections.defaultdict(list)
  for cid,r in expected.items():group[r['net_id']].append(cid)
  for net,cs in group.items():
   source=expected[cs[0]]['source'];counts=collections.Counter(n for c in cs for n in expected[c]['path'] or ());frontier={source}|{n for n in counts if geo[n][0] in ['SOURCE','OPIN','CHANX','CHANY']};assert snap['nets'][net]['references']==dict(counts) and snap['nets'][net]['frontier']==frontier and snap['nets'][net]['source']==source
   for c in cs:
    assert view.frontier(c)==frontier;checks+=1
    if expected[c]['path'] is None:
     q=view.feature(c);b=geo[expected[c]['sink']];dist=[]
     for n in frontier:
      a=geo[n]
      if a[5]==b[5]:dist.append(max(0,max(a[1],b[1])-min(a[2],b[2]))+max(0,max(a[3],b[3])-min(a[4],b[4])))
     assert q['min_tile_L1']==(min(dist) if dist else None)
 for seed in range(32):
  rng=random.Random(seed);kinds=['SOURCE','OPIN','CHANX','CHANY','CHANX','IPIN','SINK','IPIN','SINK','SOURCE'];geo={n:(kind,(x:=rng.randrange(12)),x,(y:=rng.randrange(12)),y,1 if n==9 else 0) for n,kind in enumerate(kinds)};edges=frozenset([(0,1),(9,1),(1,2),(1,3),(2,4),(3,4),(4,5),(5,6),(4,7),(7,8)]);paths={0:(0,1,2,4,5,6),1:(0,1,2,4,7,8)};alternate={0:(0,1,3,4,5,6),1:(0,1,3,4,7,8)};records=[dict(connection_id=c,net_id=0,source=0,sink=p[-1],path=list(p)) for c,p in paths.items()];expected={r['connection_id']:{**r,'path':tuple(r['path'])} for r in records};cache=Cache('graph',geo,records,lambda a,b:(a,b) in edges);original=cache.view();original_snapshot=original.snapshot();verify(original,expected,geo)
  for name,updates in [('one_sibling_parent_conflict',{0:alternate[0]}),('wrong_root',{0:(9,1,2,4,5,6)}),('missing_edge',{0:(0,3,4,5,6)}),('cycle',{0:(0,1,2,1,4,5,6)}),('unchanged',{0:paths[0]}),('foreign_CID',{99:paths[0]}),('bool_CID',{True:paths[1]}),('late_batch_failure',{0:alternate[0],1:(0,1,3,4,5,6)})]:
   reject(name,lambda u=updates:cache.prepare_paths('graph',cache.generation,u));assert cache.view().snapshot()==original_snapshot
  reject('wrong_graph',lambda:cache.prepare_paths('bad',0,alternate))
  for cycle in range(4):
   before=cache.view();before_snap=before.snapshot();token=cache.prepare('graph',cache.generation,[0]);cache.commit(token);expected[0]['path']=None;commits+=1;verify(cache.view(),expected,geo)
   target=alternate if cycle%2==0 else paths;ticket=cache.prepare_paths('graph',cache.generation,{c:list(p) for c,p in target.items()});stale=cache.prepare_paths('graph',cache.generation,{c:list(p) for c,p in target.items()});proposal=copy.deepcopy(expected)
   for c,p in target.items():proposal[c]['path']=p
   verify(cache.preview(ticket),proposal,geo);assert cache.view().query(0)['path'] is None;receipt=cache.commit(ticket);assert receipt['restored_connections']==1 and receipt['replaced_connections']==1;expected=proposal;commits+=1;verify(cache.view(),expected,geo);assert before.snapshot()==before_snap and original.snapshot()==original_snapshot;reject('stale_path_ticket',lambda:cache.commit(stale));reject('consumed_path_ticket',lambda:cache.commit(ticket))
  ticket=cache.prepare('graph',cache.generation,[],source_updates={0:9});cache.commit(ticket);commits+=1
  for r in expected.values():r.update(source=9,path=None)
  verify(cache.view(),expected,geo);assert cache.view().feature(0)['min_tile_L1'] is None
  reject('old_root_restore',lambda:cache.prepare_paths('graph',cache.generation,paths));new={c:(9,)+p[1:] for c,p in paths.items()};mutable={c:list(p) for c,p in new.items()};ticket=cache.prepare_paths('graph',cache.generation,mutable);mutable[0].clear();proposal=copy.deepcopy(expected)
  for c,p in new.items():proposal[c]['path']=p
  verify(cache.preview(ticket),proposal,geo);cache.commit(ticket);commits+=1;expected=proposal;verify(cache.view(),expected,geo);assert original.snapshot()==original_snapshot
  replacement={c:(9,)+p[1:] for c,p in alternate.items()};ticket=cache.prepare_paths('graph',cache.generation,replacement);before=cache.view().snapshot();cache.abort(ticket);assert cache.view().snapshot()==before;reject('aborted_restore',lambda:cache.commit(ticket))
 bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/retained_tree_frontier_state_v3.py',R/'tools/retained_tree_frontier_state_v2.py',R/'tools/retained_tree_frontier_state_v1.py',R/'tools/incremental_IPIN_feature_cache_v1.py']}
 with (out/'verification.json').open('x') as f:json.dump(dict(status='shared_graph_source_frontier_remove_restore_replace_root_change_cycles_pass',bindings=bindings,synthetic_graphs=32,query_state_checks=checks,commits=commits,rejected=dict(rejected),scope='Final-batch shared-parent topology and node references, endpoint-root coherence and serial publication. Not RC/capacity/legal-route admission or native/full-flow benefit.'),f,indent=2)
 print('SOURCE FRONTIER RESTORE CORE PASS',checks,commits,flush=True)
if __name__=='__main__':main()
