"""Independent one-label exact-delay feasibility; no Pareto or reverse pruning."""
import heapq
from fractions import Fraction

def query(rc,source,sink,budget,allowed,cost=None,max_labels=100000,lower=None):
    if not isinstance(budget,Fraction) or budget<0 or type(max_labels) is not int or max_labels<1:raise ValueError('invalid exact budget/limit')
    r,c=rc.node(source);rc.node(sink);initial=r*c/2;best={source:initial};parents={};settled=set();queue=[(initial,source)];examined=0
    def output(status,path=None,delay=None):
        return {'status':status,'physical_edge_ids':path,'delay':delay,'cost':None,'settled_nodes':len(settled),'discovered_nodes':len(best),'examined_edges':examined,'scope':'exact delay feasibility only; independent forward Dijkstra, no reverse/Pareto pruning'}
    if initial>budget:return output('UNREACHABLE')
    f=rc.fields
    while queue:
        delay,node=heapq.heappop(queue)
        if node in settled or best[node]!=delay:continue
        if len(settled)>=max_labels:return output('NODE_LIMIT')
        settled.add(node)
        if node==sink:
            path=[];current=sink
            while current!=source:
                current,i=parents[current];path.append(f['edge_ids'][i])
            path.reverse();assert rc.path(source,sink,path)==delay<=budget
            return output('FOUND',path,delay)
        for i in range(f['row_offsets'][node],f['row_offsets'][node+1]):
            examined+=1
            if not allowed(node,i):continue
            dest=f['dest_ranks'][i];nd=delay+rc.increment(i)
            if nd>budget or dest in settled:continue
            if dest not in best or nd<best[dest]:best[dest]=nd;parents[dest]=(node,i);heapq.heappush(queue,(nd,dest))
    return output('UNREACHABLE')
