"""Same search order/cost/context as reference; shared arcs and hash prefix."""
import hashlib,json,heapq
from normalized_rc_net_pressure import NormalizedRCNetPressure
from semantic_sketch import SearchResult

class FastNormalizedRCNetPressure(NormalizedRCNetPressure):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  self.arcs={n:tuple((eid,dst,None if w is None else w+self.full[dst]) for eid,dst,w in arcs) for n,arcs in self.base.outgoing.items()}
  self.delta={n:self.reduced[n]-self.full[n] for n in self.full if self.reduced[n]!=self.full[n]}
  self.prefix=hashlib.sha256(('{"demand": '+json.dumps(self.identity['demand'])+', "exclude": ').encode())
  self.middle=', "graph": '+json.dumps(self.identity['graph'])+', "net": '
  self.tail=', "rule": '+json.dumps(self.identity['rule'])+', "scale": '+json.dumps(self.identity['scale'])+', "table": '+json.dumps(self.identity['table'])+'}'
 def query(self,net,source,sinks,exclude=True):
  if type(net) is not int or net not in self.roots or type(source) is not int or source!=self.roots[net] or type(exclude) is not bool:raise ValueError('invalid net/source/exclude')
  own=self.users[net] if exclude else frozenset()
  h=self.prefix.copy();h.update((json.dumps(exclude)+self.middle+json.dumps(net)+', "own_nodes": '+json.dumps(sorted(own))+self.tail).encode());context=h.hexdigest()
  adjustments={n:self.delta[n] for n in own if n in self.delta}
  sinks=set(sinks);g=self.base.graph
  if source not in g.nodes or g.nodes[source].type!='SOURCE' or any(s not in g.nodes or g.nodes[s].type!='SINK' for s in sinks):raise ValueError('invalid endpoints')
  if g.nodes[source].capacity==0 or not sinks:return SearchResult({},0,0,False),context
  best={source:(0,0,())};queue=[(0,0,(),source)];settled=set();paths={};visits=0
  while queue and len(settled)<self.base.node_budget:
   cost,hops,path,node=heapq.heappop(queue)
   if node in settled or best[node]!=(cost,hops,path):continue
   settled.add(node)
   if node in sinks:
    paths[node]=path
    if len(paths)==len(sinks):break
   for eid,dst,weight in self.arcs[node]:
    visits+=1
    if dst in settled or weight is None:continue
    candidate=(cost+weight+adjustments.get(dst,0),hops+1,path+(eid,))
    if dst not in best or candidate<best[dst]:best[dst]=candidate;heapq.heappush(queue,(*candidate,dst))
  return SearchResult(paths,len(settled),visits,len(paths)<len(sinks) and len(settled)>=self.base.node_budget and bool(queue)),context
