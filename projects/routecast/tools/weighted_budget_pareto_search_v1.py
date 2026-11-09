"""Exact criticality-weighted search inside raw budget on a frozen partial tree.

Nonnegative node prices, original raw increments; capacity is a forecast price,
not a hard no-overflow restriction. Label exhaustion is UNKNOWN, never infeasible.
"""
import heapq
from fractions import Fraction

def search(offsets,dest,raw,caps,initial,target,criticality,prices,budget,bound,max_labels=10000):
    n=len(caps)
    if not isinstance(criticality,Fraction) or not 0<=criticality<=1:raise ValueError('criticality')
    if type(budget) is not int or budget<0 or type(max_labels) is not int or max_labels<1:raise ValueError('limits')
    if len(offsets)!=n+1 or offsets[-1]!=len(dest) or len(raw)!=len(dest) or not 0<=target<n:raise ValueError('graph')
    p,q=criticality.numerator,criticality.denominator;own=set(initial);labels=[];active={};heap=[];expanded=0
    def add(node,cost,delay,parent,edge):
        h=bound.get(node)
        if type(h) is not int or h<0:raise ValueError('raw lower bound')
        if delay+h>budget:return False
        old=active.setdefault(node,[])
        if any(labels[i][5] and labels[i][1]<=cost and labels[i][2]<=delay for i in old):return False
        if len(labels)>=max_labels:return None
        for i in old:
            if labels[i][1]>=cost and labels[i][2]>=delay:labels[i][5]=False
        index=len(labels);labels.append([node,cost,delay,parent,edge,True]);old.append(index);heapq.heappush(heap,(cost+p*h,cost,delay,node,index));return True
    for node,delay in sorted(initial.items()):
        if not 0<=node<n or caps[node]<=0 or type(delay) is not int or delay<0:raise ValueError('seed')
        if add(node,p*delay,delay,None,None) is None:return dict(status='UNKNOWN_LABEL_LIMIT',labels_created=len(labels),expanded=expanded)
    while heap:
        estimate,cost,delay,u,index=heapq.heappop(heap)
        if not labels[index][5]:continue
        expanded+=1
        if u==target:
            edges=[];cur=index
            while labels[cur][3] is not None:edges.append(labels[cur][4]);cur=labels[cur][3]
            edges.reverse();return dict(status='FOUND',join=labels[cur][0],path_slots=tuple(edges),raw=delay,objective_numerator=cost,objective_denominator=q,labels_created=len(labels),expanded=expanded)
        for edge in range(offsets[u],offsets[u+1]):
            v=dest[edge]
            if v in own or caps[v]<=0:continue
            price=prices.get(v,0);increment=raw[edge]
            if type(price) is not int or price<0 or type(increment) is not int or increment<0:raise ValueError('negative/noninteger cost')
            if add(v,cost+p*increment+(q-p)*price,delay+increment,index,edge) is None:return dict(status='UNKNOWN_LABEL_LIMIT',labels_created=len(labels),expanded=expanded)
    return dict(status='NO_BUDGET_PATH_FOR_FIXED_TREE',labels_created=len(labels),expanded=expanded)
