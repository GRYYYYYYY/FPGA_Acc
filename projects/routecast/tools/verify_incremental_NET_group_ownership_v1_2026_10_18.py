"""Independent query inversion oracle for incremental channel ownership."""
import hashlib,json,random
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from incremental_NET_group_ownership_v1 import Cache

def oracle(rows,groups,generation):
 inv=defaultdict(lambda:defaultdict(set));queries={}
 for row in rows:
  cid,net=row['connection_id'],row['net_id'];nodes=set(row['nodes']);queries[cid]=(net,tuple(sorted(nodes)))
  for n in nodes:inv[net][n].add(cid)
 group_of={n:g for g,ns in groups.items() for n in ns};nets={};hist=defaultdict(Counter)
 for net in {r['net_id'] for r in rows}:
  refs={n:len(cids) for n,cids in inv[net].items()};ks=Counter(group_of[n] for n in refs);nets[net]=(refs,dict(ks))
  for g,k in ks.items():hist[g][k]+=1
 features={}
 for g,ns in groups.items():
  # Enumerate every NET's ownership directly, not histogram helper.
  loads=[sum(n in inv[net] for n in ns) for net in inv];m=len(ns)
  mean=sum((Fraction(k,m) for k in loads),Fraction(0));empty=Fraction(1)
  for k in loads:empty*=Fraction(m-k,m)
  features[g]=(mean,empty,mean-1+empty)
 return dict(generation=generation,queries=queries,nets=nets,histograms={g:dict(h) for g,h in hist.items()},features=features)

def main():
 out=Path('experiments/incremental_NET_group_ownership_core_v1_2026-10-18');out.mkdir(exist_ok=False)
 groups={0:[0,1,2],1:[3,4],2:[5],3:[6,7]};rng=random.Random(3184)
 rows=[dict(connection_id=i,net_id=i//3,nodes=[0,0,3] if i<3 else []) for i in range(30)]
 cache=Cache('graph',groups,rows);assert cache.snapshot()==oracle(rows,groups,0)
 rejects=0;shared_reference_events=0
 for step in range(500):
  target=[dict(r,nodes=list(r['nodes'])) for r in rows]
  for i in rng.sample(range(30),rng.randint(1,8)):target[i]['nodes']=rng.sample(range(8),rng.randint(0,8))
  delta=[dict(old=a,new=b) for a,b in zip(rows,target) if set(a['nodes'])!=set(b['nodes'])]
  if not delta:continue
  before=cache.snapshot();ticket=cache.prepare('graph',cache.generation,delta);stale=cache.prepare('graph',cache.generation,delta)
  assert cache.snapshot()==before
  result=cache.commit(ticket);rows=target;assert cache.snapshot()==oracle(rows,groups,cache.generation)
  if result['reference_events']>result['ownership_events']:shared_reference_events+=1
  for token in [ticket,stale,object()]:
   before=cache.snapshot()
   try:cache.commit(token)
   except ValueError:rejects+=1
   else:raise AssertionError('ticket rejection')
   assert cache.snapshot()==before
 # A sibling's removal keeps the shared NET-node; final sibling removal clears it.
 tiny=[dict(connection_id=i,net_id=0,nodes=[0,0]) for i in range(2)];c=Cache('g',groups,tiny)
 for i in range(2):
  new=dict(tiny[i],nodes=[]);c.commit(c.prepare('g',i,[dict(old=tiny[i],new=new)]));tiny[i]=new
  assert c.snapshot()==oracle(tiny,groups,i+1)
  assert bool(c.snapshot()['nets'][0][0])==(i==0)
 assert shared_reference_events>0
 bindings={str(Path(p).resolve()):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in [__file__,'tools/incremental_NET_group_ownership_v1.py','tools/incremental_IPIN_feature_cache_v1.py','tools/net_group_collision_risk_v1.py']}
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,random_steps=500,rejected_tickets=rejects,steps_with_shared_reference_events=shared_reference_events,explicit='repeated node projection deduplication, sibling shared ownership and last-reference deletion',scope='Synthetic accounting core only; real archived path projection, illegal edit fixtures, joint endpoint/path publication and utility still pending.'),f,indent=2)
 print(json.dumps(dict(status='pass',steps=500,rejected_tickets=rejects,shared_reference_steps=shared_reference_events)))
if __name__=='__main__':main()
