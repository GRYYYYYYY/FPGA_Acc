"""Independent full-domain score oracle and serial publication rejection audit."""
import hashlib,json,random
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
import joint_full_score_state_v1 as core

def expected(rows,groups,capacities):
 owners=defaultdict(set)
 for r in rows:
  for n in set(r['nodes']):owners[n].add(r['net_id'])
 scores={n:(float(Fraction(max(0,len(owners[n])-cap),cap)),)*2 for n,cap in capacities.items()}
 for gid,nodes in groups.items():
  ks=Counter(net for n in nodes for net in owners[n]);m=len(nodes);mean=Fraction(sum(ks.values()),m);empty=Fraction(1)
  for k in ks.values():empty*=Fraction(m-k,m)
  value=(float(mean),float(mean-1+empty))
  for n in nodes:scores[n]=value
 return scores

def verify(view,rows,groups,capacities):
 assert view.component_generations==(view.generation,view.generation)
 for r in rows:assert view.query(r['connection_id'])==dict(r,nodes=sorted(set(r['nodes'])))
 for n,value in expected(rows,groups,capacities).items():assert view.score(n)==value,(n,view.score(n),value)

def main():
 out=Path('experiments/joint_full_score_state_core_v1_2026-10-18');out.mkdir(exist_ok=False)
 groups={0:[300,301,302],1:[303,304],2:[210,211],3:[212,213]};sinkgroups={200:2,201:3};sources={100,101}
 capacities={n:1 for ns in groups.values() for n in ns};capacities.update({100:2,101:2,200:3,201:3,400:2,401:1})
 def row(cid,net,source,sink,channels,opin=400):return dict(connection_id=cid,net_id=net,source=source,sink=sink,nodes=sorted({source,sink,210+2*(sink-200)+net%2,opin,*channels}))
 rows=[row(i,i//2,100,200,[300]) for i in range(12)];obj=core.Joint('g',groups,sinkgroups,sources,capacities,rows);verify(obj.view(),rows,groups,capacities)
 assert obj.view().score(400)==(2.,2.)
 rng=random.Random(9481);rejects=[]
 def reject(name,fn,exception=ValueError):
  old=obj.view();before=[old.query(i) for i in range(12)]
  try:fn()
  except exception:pass
  else:raise AssertionError(name)
  assert [obj.view().query(i) for i in range(12)]==before
  verify(obj.view(),rows,groups,capacities);rejects.append(name)
 accepted=0
 for step in range(200):
  target=[dict(r,nodes=list(r['nodes'])) for r in rows]
  for i in rng.sample(range(12),rng.randint(1,4)):
   r=target[i];target[i]=row(i,r['net_id'],r['source'],rng.choice([200,201]),rng.sample(range(300,305),rng.randint(0,5)),rng.choice([400,401]))
  if step%6==0:
   net=rng.randrange(6)
   for i,r in enumerate(target):
    if r['net_id']==net:
     new=201-r['source'];target[i]=dict(r,source=new,nodes=sorted(set(r['nodes'])-{r['source']}|{new}))
  delta=[dict(old=a,new=b) for a,b in zip(rows,target) if a!=b]
  if not delta:continue
  oldview=obj.view();ticket=obj.prepare('g',oldview.generation,delta);stale=obj.prepare('g',oldview.generation,delta)
  verify(obj.view(),rows,groups,capacities)
  # Caller edits after prepare cannot alter the staged version.
  delta[0]['new']['nodes'].clear()
  obj.commit(ticket);verify(oldview,rows,groups,capacities);rows=target
  # target rows shared the caller's descriptor; reconstruct canonical rows from view.
  rows=[obj.view().query(i) for i in range(12)];verify(obj.view(),rows,groups,capacities);accepted+=1
  reject('replayed',lambda:obj.commit(ticket));reject('stale_ticket',lambda:obj.commit(stale));reject('foreign',lambda:obj.commit(object()))
 # Focused bad update constructors; all leave the published state intact.
 a=rows[0];b=row(0,a['net_id'],a['source'],a['sink'],[300] if 300 not in a['nodes'] else [301])
 def attempt(old,new):return obj.prepare('g',obj.view().generation,[dict(old=old,new=new)])
 reject('wrong_graph',lambda:obj.prepare('other',obj.view().generation,[dict(old=a,new=b)]))
 reject('wrong_generation',lambda:obj.prepare('g',-1,[dict(old=a,new=b)]))
 reject('missing_SOURCE',lambda:attempt(a,dict(b,nodes=[n for n in b['nodes'] if n!=b['source']])))
 reject('wrong_IPIN_class',lambda:attempt(a,dict(b,nodes=[n for n in b['nodes'] if n not in [210,211,212,213]]+[212 if b['sink']==200 else 210])))
 reject('unknown_node',lambda:attempt(a,dict(b,nodes=b['nodes']+[999])))
 reject('NET_change',lambda:attempt(a,dict(b,net_id=999)))
 reject('duplicate_CID',lambda:obj.prepare('g',obj.view().generation,[dict(old=a,new=b)]*2))
 # Partial driver update with otherwise consistent projected endpoints.
 source=201-a['source'];changed=dict(a,source=source,nodes=sorted(set(a['nodes'])-{a['source']}|{source}))
 reject('partial_NET_driver',lambda:attempt(a,changed))
 saved=core.patched
 def fail(*args):raise MemoryError('injected final score allocation failure')
 core.patched=fail;reject('score_allocation_failure',lambda:attempt(a,b),MemoryError);core.patched=saved
 # Zeroing endpoint demand class and path-only commits preserve all generations.
 tiny=[row(0,0,100,200,[300])];t=core.Joint('g',groups,sinkgroups,sources,capacities,tiny)
 dest=[row(0,0,100,201,[300])];t.commit(t.prepare('g',0,[dict(old=tiny[0],new=dest[0])]))
 verify(t.view(),dest,groups,capacities);assert t.view().score(210)==(0.,0.)
 final=[row(0,0,100,201,[301])];receipt=t.commit(t.prepare('g',1,[dict(old=dest[0],new=final[0])]))
 verify(t.view(),final,groups,capacities);assert receipt['endpoint_updates']==0 and t.view().component_generations==(2,2)
 files=[__file__,'tools/joint_full_score_state_v1.py','tools/incremental_IPIN_feature_cache_v1.py','tools/incremental_NET_group_ownership_v1.py','tools/net_group_collision_risk_v1.py']
 bindings={str(Path(p).resolve()):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files}
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,random_attempts=200,accepted_batches=accepted,rejections=len(rejects),focused_rejections=rejects[-9:],fixed_capacity2_overflow_checked=True,zero_demand_and_path_only_generations_checked=True,scope='Synthetic full positive-domain typed mean/collision score publication only; no physical/RC legality, real full-vector replay or full-flow utility evidence.'),f,indent=2)
 print(json.dumps(dict(status='pass',accepted_batches=accepted,rejections=len(rejects))))
if __name__=='__main__':main()
