"""Exact signed integer node potentials for directed arc difference equations."""
class Potentials:
 def __init__(self,n):
  self.parent=list(range(n));self.rank=[0]*n;self.offset=[0]*n
 def find(self,node):
  trail=[];u=node;total=0
  while self.parent[u]!=u:
   trail.append((u,self.offset[u]));total+=self.offset[u];u=self.parent[u]
  remaining=total
  for v,delta in trail:self.parent[v]=u;self.offset[v]=remaining;remaining-=delta
  return u,total
 def constrain(self,source,sink,cost):
  a,du=self.find(source);b,dv=self.find(sink)
  if a==b:return 'consistent' if dv-du==cost else 'conflict'
  difference=cost+du-dv
  if self.rank[a]<self.rank[b]:self.parent[a]=b;self.offset[a]=-difference
  else:
   self.parent[b]=a;self.offset[b]=difference
   if self.rank[a]==self.rank[b]:self.rank[a]+=1
  return 'merged'
