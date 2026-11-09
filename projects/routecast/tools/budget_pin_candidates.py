"""Exact nonnegative two-resource labels: minimum arc cost within delay budget.

Fixed physical SOURCE/target pin, optional forbidden resources/arcs. A label
limit is reported distinctly from infeasibility; no path is published on limit.
"""
import heapq
from collections import defaultdict
from reachable_pin_candidates import ReachablePins

class BudgetPins(ReachablePins):
 def __init__(self,graph):
  super().__init__(graph);incoming=defaultdict(list)
  for eid,edge in enumerate(graph.edges):incoming[edge.sink].append(eid)
  self.incoming=incoming
 def query(self,source,sink,source_ptc,target_ptc,edge_costs,edge_delays,budget,blocked_nodes=(),blocked_edges=(),max_labels=500000):
  if type(source) is not int or source not in self.catalog.sources:raise ValueError('invalid SOURCE')
  if type(sink) is not int or sink not in self.catalog.sinks:raise ValueError('invalid SINK')
  if type(source_ptc) is not int or source_ptc not in self.catalog.sources[source].physical_pins:raise ValueError('invalid source pin')
  if type(target_ptc) is not int or target_ptc not in self.catalog.sinks[sink].physical_pins:raise ValueError('invalid target pin')
  if type(budget) is not int or budget<0 or type(max_labels) is not int or max_labels<1:raise ValueError('invalid budget/label limit')
  costs=tuple(edge_costs);delays=tuple(edge_delays);size=len(self.graph.edges)
  if len(costs)!=size or len(delays)!=size or any(type(v) is not int or v<0 for v in costs+delays):raise ValueError('nonnegative integer arc vectors required')
  blocked=frozenset(blocked_nodes);forbidden=frozenset(blocked_edges)
  if any(type(n) is not int or n not in self.graph.nodes or self.graph.nodes[n].type not in {'CHANX','CHANY'} for n in blocked):raise ValueError('invalid blocked channel')
  if any(type(e) is not int or not 0<=e<size for e in forbidden):raise ValueError('invalid blocked edge')
  opins=set(self.catalog.sources[source].physical_pins[source_ptc]);targets=set(self.catalog.sinks[sink].physical_pins[target_ptc]);allowed_nodes={source,sink}|opins|targets|{n for n,v in self.graph.nodes.items() if v.type in {'CHANX','CHANY'} and v.capacity>0 and n not in blocked}
  def allowed(eid):
   if eid in forbidden:return False
   edge=self.graph.edges[eid];a,b=edge.source,edge.sink
   if a not in allowed_nodes or b not in allowed_nodes or b in blocked or self.graph.nodes[b].capacity<=0:return False
   if a==source:return b in opins
   if a in targets:return b==sink
   if a==sink:return False
   return self.graph.nodes[b].type in {'CHANX','CHANY'} or b in targets
  # Exact reverse minimum-delay lower bound under the same pin/arc constraints.
  lower={sink:0};reverse=[(0,sink)];reverse_settled=set();reverse_examined=0
  while reverse:
   # No prefix with nonnegative delay can use a suffix above the budget.
   if reverse[0][0]>budget:break
   value,node=heapq.heappop(reverse)
   if node in reverse_settled or lower[node]!=value:continue
   reverse_settled.add(node)
   for eid in self.incoming[node]:
    reverse_examined+=1
    if not allowed(eid):continue
    parent=self.graph.edges[eid].source;candidate=value+delays[eid]
    if parent not in lower or candidate<lower[parent]:lower[parent]=candidate;heapq.heappush(reverse,(candidate,parent))
  labels=[];front=defaultdict(list);queue=[];expanded=0;examined=0
  def output(status,path=None,cost=None,delay=None):return {'status':status,'path':path,'cost':cost,'delay':delay,'labels_created':len(labels),'labels_expanded':expanded,'examined_edges':examined,'reverse_settled_nodes':len(reverse_settled),'reverse_examined_edges':reverse_examined,'budget':budget,'max_labels':max_labels,'scope':'minimum supplied additive cost under supplied integer delay budget and fixed pin constraints; not joint net or native timing legality'}
  if source not in lower or lower[source]>budget:return output('UNREACHABLE')
  # Label tuple: node,cost,delay,parent label ID,parent edge ID,active.
  labels.append([source,0,0,None,None,True]);front[source]=[0];queue=[(0,0,source,0)]
  while queue:
   cost,delay,node,lid=heapq.heappop(queue)
   if not labels[lid][5]:continue
   expanded+=1
   if node==sink:
    path=[];cursor=lid
    while labels[cursor][3] is not None:path.append(labels[cursor][4]);cursor=labels[cursor][3]
    path.reverse();w=self.catalog.witness(source,sink,path);assert w['selected_opin_ptc']==source_ptc and w['selected_ipin_ptc']==target_ptc;assert sum(costs[e] for e in path)==cost and sum(delays[e] for e in path)==delay and delay<=budget;return output('FOUND',path,cost,delay)
   for eid in self.outgoing[node]:
    examined+=1
    if not allowed(eid):continue
    dest=self.graph.edges[eid].sink;nc=cost+costs[eid];nd=delay+delays[eid]
    if dest not in lower or nd+lower[dest]>budget:continue
    old=front[dest]
    if any(labels[x][1]<=nc and labels[x][2]<=nd for x in old):continue
    if len(labels)>=max_labels:return output('LABEL_LIMIT')
    keep=[]
    for x in old:
     if nc<=labels[x][1] and nd<=labels[x][2]:labels[x][5]=False
     else:keep.append(x)
    new=len(labels);labels.append([dest,nc,nd,lid,eid,True]);front[dest]=keep+[new];heapq.heappush(queue,(nc,nd,dest,new))
  return output('UNREACHABLE')
