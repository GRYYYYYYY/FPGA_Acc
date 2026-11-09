"""Host proof prototype: immutable settled parents and one heap slot per node.

Full physical-node budget only. Tie comparisons reconstruct paths temporarily;
this verifies semantics, not an efficient or synthesizable hardware comparator.
"""
from semantic_sketch import SearchResult
class PredecessorSearch:
 def __init__(self,engine):
  self.engine=engine
  if engine.node_budget<len(engine.graph.nodes):raise ValueError('full node budget required')
 def search(self,source,sinks):
  sinks=set(sinks);g=self.engine.graph
  if source not in g.nodes or g.nodes[source].type!='SOURCE' or any(s not in g.nodes or g.nodes[s].type!='SINK' for s in sinks):raise ValueError('invalid endpoints')
  if not sinks or not g.nodes[source].capacity:return SearchResult({},0,0,False)
  labels={source:(0,0,None,None)};heap=[];positions={};settled=set();paths={};visits=0;peak=0
  def path(node):
   edges=[]
   while labels[node][2] is not None:
    _,_,parent,eid=labels[node];edges.append(eid);node=parent
   return tuple(reversed(edges))
  def less(a,b):
   la,lb=labels[a],labels[b]
   if la[:2]!=lb[:2]:return la[:2]<lb[:2]
   return (path(a),a)<(path(b),b)
  def swap(a,b):
   heap[a],heap[b]=heap[b],heap[a];positions[heap[a]]=a;positions[heap[b]]=b
  def up(i):
   while i:
    p=(i-1)//2
    if not less(heap[i],heap[p]):break
    swap(i,p);i=p
  def push_or_decrease(node):
   if node not in positions:positions[node]=len(heap);heap.append(node)
   up(positions[node])
  push_or_decrease(source)
  while heap:
   peak=max(peak,len(heap));node=heap[0];last=heap.pop();del positions[node]
   if heap:
    heap[0]=last;positions[last]=0;i=0
    while 2*i+1<len(heap):
     child=2*i+1
     if child+1<len(heap) and less(heap[child+1],heap[child]):child+=1
     if not less(heap[child],heap[i]):break
     swap(i,child);i=child
   settled.add(node)
   if node in sinks:
    paths[node]=path(node)
    if len(paths)==len(sinks):break
   cost,hops,_,_=labels[node]
   for eid,dst,w in self.engine.outgoing[node]:
    visits+=1
    if dst in settled or w is None:continue
    if type(w) is not int or w<0:raise ValueError('invalid additive cost')
    candidate=(cost+w,hops+1,node,eid);old=labels.get(dst)
    better=old is None or candidate[:2]<old[:2]
    if old is not None and candidate[:2]==old[:2]:better=path(node)+(eid,)<path(dst)
    if better:labels[dst]=candidate;push_or_decrease(dst)
  self.last_peak_frontier=peak
  assert peak<=len(g.nodes)
  return SearchResult(paths,len(settled),visits,False)
