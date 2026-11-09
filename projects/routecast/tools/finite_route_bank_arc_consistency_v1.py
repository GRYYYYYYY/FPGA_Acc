"""Sound binary capacity/shared-parent arc consistency with replayable removals."""
from collections import deque,defaultdict
def propagate(bank,queries,capacities):
 domains={c:set(range(len(options))) for c,options in bank.items()};data={}
 for c,options in bank.items():
  for i,option in enumerate(options):
   path=option['path'];data[c,i]=({n for n,s in path},{v:(u,s) for (u,_),(v,s) in zip(path,path[1:])})
 bad={};neighbors=defaultdict(set)
 for a in sorted(bank):
  for b in sorted(bank):
   if b<=a:continue
   pairs=set();same=queries[a]['net_id']==queries[b]['net_id']
   for i in domains[a]:
    an,ap=data[a,i]
    for j in domains[b]:
     bn,bp=data[b,j];conflict=any(ap[n]!=bp[n] for n in ap.keys()&bp.keys()) if same else any(capacities[n]<2 for n in an&bn)
     if conflict:pairs.add((i,j))
   if pairs:
    bad[a,b]=pairs;bad[b,a]={(j,i) for i,j in pairs};neighbors[a].add(b);neighbors[b].add(a)
 queue=deque(sorted(bad));removed=[]
 while queue:
  a,b=queue.popleft();changed=False
  for i in sorted(domains[a]):
   if all((i,j) in bad[a,b] for j in domains[b]):
    removed.append(dict(connection=a,index=i,blocker=b,blocker_domain=sorted(domains[b])));domains[a].remove(i);changed=True
  if not domains[a]:return dict(status='FINITE_BANK_BINARY_CONFLICT',empty_connection=a,removals=removed,domains={str(c):sorted(v) for c,v in domains.items()})
  if changed:
   for other in sorted(neighbors[a]-{b}):queue.append((other,a))
 return dict(status='ARC_CONSISTENT',empty_connection=None,removals=removed,domains={str(c):sorted(v) for c,v in domains.items()})
