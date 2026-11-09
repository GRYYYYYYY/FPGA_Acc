"""Bounded exact reverse Dijkstra; unfinished frontier remains admissible.

CSR and electrical context must already be authenticated. Incoming arc index
is separate reusable topology, never a full delay vector. Arc eligibility must
be identical to forward search. Unsettled tentative distances are never bounds.
"""
from array import array
import heapq
from fractions import Fraction

def incoming(fields):
    n=len(fields['node_ids']);counts=array('Q',[0])*n
    for d in fields['dest_ranks']:counts[d]+=1
    offsets=array('Q',[0])
    for v in counts:offsets.append(offsets[-1]+v)
    cursor=array('Q',offsets[:-1]);indices=array('Q',[0])*len(fields['edge_ids']);parents=array('Q',[0])*len(fields['edge_ids'])
    for src in range(n):
        for i in range(fields['row_offsets'][src],fields['row_offsets'][src+1]):
            d=fields['dest_ranks'][i];j=cursor[d];indices[j]=i;parents[j]=src;cursor[d]+=1
    return offsets,indices,parents

class Bound:
    def __init__(self,settled,frontier,complete,counters):
        self.settled=settled;self.frontier=frontier;self.complete=complete;self.counters=counters
    def __call__(self,node):
        return self.settled.get(node,None if self.complete else self.frontier)

def prepare(rc,reverse,sink,allowed,max_settled=100000):
    rc.node(sink)
    if type(max_settled) is not int or max_settled<1:raise ValueError('positive reverse limit required')
    rows,arcs,parents=reverse;tentative={sink:Fraction(0)};queue=[(Fraction(0),sink)];settled={};examined=0
    while queue:
        value,node=heapq.heappop(queue)
        if node in settled or tentative[node]!=value:continue
        if len(settled)>=max_settled:
            return Bound(settled,value,False,{'settled':len(settled),'examined':examined,'complete':False})
        settled[node]=value
        for j in range(rows[node],rows[node+1]):
            examined+=1;i=arcs[j];parent=parents[j]
            if parent in settled or not allowed(parent,i):continue
            candidate=value+rc.increment(i)
            if parent not in tentative or candidate<tentative[parent]:tentative[parent]=candidate;heapq.heappush(queue,(candidate,parent))
    return Bound(settled,None,True,{'settled':len(settled),'examined':examined,'complete':True})
