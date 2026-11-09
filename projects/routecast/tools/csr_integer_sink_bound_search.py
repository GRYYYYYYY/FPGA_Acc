"""Sparse Pareto search with exact buffered RC budget over authenticated CSR.

Independent sink-bound pruning policy. Caller authenticates exact shortest remaining RC lower bounds over the same eligible directed graph, nonnegative additive delays/objective. Label/resource behavior intentionally differs from unpruned search.
No joint-net legality, pin equivalence or occupancy certificate is inferred.
"""
import heapq
from fractions import Fraction

def query(rc,source,sink,budget,allowed,cost,remaining,max_labels=100000):
    if type(budget) is not int or budget<0 or type(max_labels) is not int or max_labels<1:
        raise ValueError('exact scaled integer budget and positive label limit required')
    rc.node(source);rc.node(sink);initial=rc.initial(source);f=rc.fields
    labels=[];front={};queue=[];expanded=0;examined=0
    def result(status,lid=None):
        path=None;objective=None;delay=None
        if lid is not None:
            objective=labels[lid][1];delay=labels[lid][2];path=[];cursor=lid
            while labels[cursor][3] is not None:
                path.append(f['edge_ids'][labels[cursor][4]]);cursor=labels[cursor][3]
            path.reverse()
            if rc.path(source,sink,path)!=delay or delay>budget:raise ValueError('invalid search witness')
        return {'status':status,'physical_edge_ids':path,'cost':objective,'delay':delay,'labels_created':len(labels),'labels_expanded':expanded,'examined_edges':examined}
    if source not in remaining or initial+remaining[source]>budget:return result('UNREACHABLE')
    labels.append([source,0,initial,None,None,True]);front[source]=[0];queue=[(0,initial,source,0)]
    while queue:
        objective,delay,node,lid=heapq.heappop(queue)
        if not labels[lid][5]:continue
        expanded+=1
        if node==sink:return result('FOUND',lid)
        for i in range(f['row_offsets'][node],f['row_offsets'][node+1]):
            examined+=1
            if not allowed(node,i):continue
            dest=f['dest_ranks'][i];nd=delay+rc.increment(i)
            if dest not in remaining or nd+remaining[dest]>budget:continue
            w=cost(node,i)
            if type(w) is not int or w<0:raise ValueError('nonnegative integer objective required')
            nc=objective+w
            if nd>budget:continue
            old=front.get(dest,[])
            if any(labels[x][1]<=nc and labels[x][2]<=nd for x in old):continue
            if len(labels)>=max_labels:return result('LABEL_LIMIT')
            keep=[]
            for x in old:
                if nc<=labels[x][1] and nd<=labels[x][2]:labels[x][5]=False
                else:keep.append(x)
            new=len(labels);labels.append([dest,nc,nd,lid,i,True]);front[dest]=keep+[new];heapq.heappush(queue,(nc,nd,dest,new))
    return result('UNREACHABLE')
