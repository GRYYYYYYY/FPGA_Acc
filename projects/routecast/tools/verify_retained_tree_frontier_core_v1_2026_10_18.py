"""Independent retained-path unions, geometry and serial transaction properties."""
import copy,hashlib,json,random,sys
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from retained_tree_frontier_state_v1 import Cache
from pre_route_endpoints import sha

def main():
 out=R/'experiments/retained_tree_frontier_core_v1_2026-10-18';out.mkdir(exist_ok=False);checks=commits=0;rejected=Counter()
 def reject(name,fn):
  try:fn()
  except ValueError:rejected[name]+=1
  else:raise AssertionError(name)
 def verify(view,expected,geo):
  nonlocal checks
  snap=view.snapshot();assert set(snap['queries'])==set(expected);nets=defaultdict(list)
  for cid,r in expected.items():assert view.query(cid)==r;nets[r['net_id']].append(cid)
  for net,cids in nets.items():
   source=expected[cids[0]]['source'];assert all(expected[c]['source']==source for c in cids);counts=Counter(n for c in cids for n in expected[c]['path'] or ());wanted={source}|{n for n in counts if geo[n][0] in ['SOURCE','OPIN','CHANX','CHANY']};actual=snap['nets'][net];assert actual['source']==source and actual['cids']==set(cids) and actual['references']==dict(counts) and actual['frontier']==wanted
   for cid in cids:
    assert view.frontier(cid)==wanted
    if expected[cid]['path'] is None:
     v=view.feature(cid);b=geo[expected[cid]['sink']];dist=[]
     for n in wanted:
      a=geo[n]
      if a[5]!=b[5]:continue
      x=b[1]-a[2] if a[2]<b[1] else a[1]-b[2] if b[2]<a[1] else 0;y=b[3]-a[4] if a[4]<b[3] else a[3]-b[4] if b[4]<a[3] else 0;dist.append(x+y)
     assert v['min_tile_L1']==(min(dist) if dist else None) and v['same_layer_frontier_nodes']==len(dist) and v['frontier_nodes']==len(wanted) and v['graph_epoch']==view.graph_epoch and v['published']==view.published
    else:reject('retained_query_feature_leak',lambda c=cid:view.feature(c))
    checks+=1
 for seed in range(24):
  rng=random.Random(seed);geo={};edges=set();records=[];nid=0;cid=0;sources=[];new_sources=[]
  for net in range(3):
   root=nid;nid+=1;sources.append(root);geo[root]=['SOURCE',0,0,0,0,0];trunk=nid;nid+=1;geo[trunk]=['OPIN',0,0,0,0,0];edges.add((root,trunk));paths={trunk:[root,trunk]};choices=[trunk]
   for j in range(7):
    parent=rng.choice(choices);n=nid;nid+=1;x,y=rng.randrange(9),rng.randrange(9);geo[n]=['CHANX' if j%2 else 'CHANY',x,x+rng.randrange(3),y,y+rng.randrange(3),0];edges.add((parent,n));paths[n]=paths[parent]+[n];choices.append(n)
   for j in range(7):
    parent=rng.choice(choices);pin=nid;sink=nid+1;nid+=2;x,y=rng.randrange(12),rng.randrange(12);geo[pin]=['IPIN',x,x,y,y,0];geo[sink]=['SINK',x,x,y,y,0];edges.update([(parent,pin),(pin,sink)]);records.append(dict(connection_id=cid,net_id=net,source=root,sink=sink,path=paths[parent]+[pin,sink]));cid+=1
   n=nid;nid+=1;geo[n]=['SOURCE',20,20,20,20,seed%2];new_sources.append(n)
  original=copy.deepcopy(records);expected={r['connection_id']:{**r,'path':tuple(r['path'])} for r in original};epoch=hashlib.sha256(str(seed).encode()).hexdigest();cache=Cache(epoch,geo,records,lambda a,b:(a,b) in edges);old=cache.view();verify(old,expected,geo);saved=old.snapshot();records[0]['path'].clear();assert old.snapshot()==saved
  reject('wrong_graph',lambda:cache.prepare('wrong',0,[0]));reject('duplicate_CID',lambda:cache.prepare(epoch,0,[0,0]));reject('unknown_CID',lambda:cache.prepare(epoch,0,[999]));reject('sink_without_removal',lambda:cache.prepare(epoch,0,[0],{1:original[1]['sink']}));reject('bad_source_type',lambda:cache.prepare(epoch,0,[],source_updates={0:original[0]['sink']}));reject('bad_sink_type',lambda:cache.prepare(epoch,0,[0],{0:sources[0]}));assert cache.view().snapshot()==saved
  for step in range(5):
   active=[c for c,r in expected.items() if r['path'] is not None]
   if not active:break
   removed=rng.sample(active,min(2,len(active)));sink_updates={removed[0]:rng.choice(original)['sink']};source_updates={1:new_sources[1]} if step==2 else {};before=cache.view();before_snap=before.snapshot();proposal=copy.deepcopy(expected);remove_set=set(removed)
   for net,src in source_updates.items():remove_set.update(c for c,r in proposal.items() if r['net_id']==net)
   for c in remove_set:
    r=proposal[c];r.update(path=None,source=source_updates.get(r['net_id'],r['source']),sink=sink_updates.get(c,r['sink']))
   token=cache.prepare(epoch,cache.generation,removed,sink_updates,source_updates);stale=cache.prepare(epoch,cache.generation,removed,sink_updates,source_updates);assert not cache.preview(token).published;verify(cache.preview(token),proposal,geo);assert cache.view().snapshot()==before_snap;receipt=cache.commit(token);assert receipt['generation']==before.generation+1;expected=proposal;verify(cache.view(),expected,geo);assert before.snapshot()==before_snap and old.snapshot()==saved;reject('stale_commit',lambda:cache.commit(stale));reject('consumed_commit',lambda:cache.commit(token));reject('old_generation',lambda:cache.prepare(epoch,before.generation,removed));commits+=1
  active=[c for c,r in expected.items() if r['path'] is not None]
  if active:
   before=cache.view().snapshot();ticket=cache.prepare(epoch,cache.generation,[active[0]]);cache.abort(ticket);assert cache.view().snapshot()==before;reject('aborted_commit',lambda:cache.commit(ticket))
  bad=copy.deepcopy(original);bad[0]['path'][1]=bad[0]['source'];reject('path_cycle',lambda:Cache(epoch,geo,bad,lambda a,b:(a,b) in edges));reject('missing_edge',lambda:Cache(epoch,geo,original,lambda a,b:False))
 bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/retained_tree_frontier_state_v1.py',R/'tools/incremental_IPIN_feature_cache_v1.py']}
 with (out/'verification.json').open('x') as f:json.dump(dict(status='source_frontier_core_independent_unions_geometry_and_transactions_pass',bindings=bindings,synthetic_graphs=24,query_state_checks=checks,commits=commits,rejected=dict(rejected),scope='Source-only retained ordered-path unions, same-layer rectangle gap and serial COW/CAS. Not native frontier parity, legal reroute repair, RouteCast integration, hardware or complete-time gain. Real admitted frame and cost validation pending.'),f,indent=2)
 print('SOURCE FRONTIER CORE PASS',checks,commits,flush=True)
if __name__=='__main__':main()
