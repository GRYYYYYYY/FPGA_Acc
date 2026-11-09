"""Lossless integer scaling of finite node/switch RC classes, not rounding.

Only class/switch combinations are materialized, never full edge weights.
A fractional budget maps to floor(budget*scale) because every path delay is
on the exact integer lattice. Scope remains buffered zero-Cinternal RC only.
"""
from fractions import Fraction
from math import lcm
from buffered_rc_node_classes import arc_delay

class IntegerRC:
    def __init__(self,rc):
        self.rc=rc;self.fields=rc.fields
        starts=[r*c/2 for r,c in rc.classes]
        values={(cid,sid):arc_delay(rc.classes,rc.switches,cid,sid) for cid in range(len(rc.classes)) for sid in rc.switches}
        self.scale=1
        for value in [*starts,*values.values()]:self.scale=lcm(self.scale,value.denominator)
        self.starts=[int(value*self.scale) for value in starts]
        self.weights={k:int(value*self.scale) for k,value in values.items()}
    def increment(self,i):
        if type(i) is not int or not 0<=i<len(self.fields['edge_ids']):raise ValueError('invalid arc')
        return self.weights[self.rc.node_classes[self.fields['dest_ranks'][i]],self.fields['switch_ids'][i]]
    def path(self,source,sink,path):return int(self.rc.path(source,sink,path)*self.scale)

def query(context,source,sink,budget,allowed,max_nodes=100000):
    # Use a separate integer search: Fraction-only reference remains unchanged.
    import heapq
    if not isinstance(budget,Fraction) or budget<0 or type(max_nodes) is not int or max_nodes<1:raise ValueError('invalid budget/limit')
    context.rc.node(source);context.rc.node(sink);initial=context.starts[context.rc.node_classes[source]];threshold=(budget.numerator*context.scale)//budget.denominator
    f=context.fields;best={source:initial};parents={};settled=set();queue=[(initial,source)];examined=0
    def output(status,path=None,delay=None):
        return {'status':status,'physical_edge_ids':path,'delay':None if delay is None else Fraction(delay,context.scale),'settled_nodes':len(settled),'discovered_nodes':len(best),'examined_edges':examined}
    if initial>threshold:return output('UNREACHABLE')
    while queue:
        delay,node=heapq.heappop(queue)
        if node in settled or best[node]!=delay:continue
        if len(settled)>=max_nodes:return output('NODE_LIMIT')
        settled.add(node)
        if node==sink:
            path=[];n=sink
            while n!=source:n,i=parents[n];path.append(f['edge_ids'][i])
            path.reverse();assert context.path(source,sink,path)==delay<=threshold
            return output('FOUND',path,delay)
        for i in range(f['row_offsets'][node],f['row_offsets'][node+1]):
            examined+=1
            if not allowed(node,i):continue
            d=f['dest_ranks'][i];nd=delay+context.increment(i)
            if nd>threshold or d in settled:continue
            if d not in best or nd<best[d]:best[d]=nd;parents[d]=(node,i);heapq.heappush(queue,(nd,d))
    return output('UNREACHABLE')
