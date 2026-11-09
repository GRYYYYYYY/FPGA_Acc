"""Sufficient local RR automorphisms: equal metadata and exact weighted rows/columns.

Only CHAN nodes participate. Metadata excludes node ID and track ptc, retaining
capacity, geometry, direction, segment and electrical attributes. Edges retain
switch IDs and multiplicity. This is not a complete graph automorphism solver.
"""
from collections import defaultdict,Counter

class Builder:
    def __init__(self):self.meta={};self.out={};self.inc={};self.edges=0
    def node(self,n,metadata):
        if n in self.meta:raise ValueError('duplicate channel')
        self.meta[n]=metadata;self.out[n]=[];self.inc[n]=[]
    def edge(self,u,v,s):
        self.edges+=1
        if u in self.out:self.out[u].append((v,s))
        if v in self.inc:self.inc[v].append((u,s))
    def classes(self):
        bins=defaultdict(list)
        for n in self.meta:
            self.out[n]=tuple(sorted(self.out[n]));self.inc[n]=tuple(sorted(self.inc[n]))
            bins[self.meta[n],self.out[n],self.inc[n]].append(n)
        return [tuple(sorted(v)) for v in bins.values() if len(v)>1]
    def verify_swap(self,a,b):
        if self.meta[a]!=self.meta[b]:raise ValueError('metadata differs')
        pair={a,b};edges=Counter()
        for u in [a,b]:
            edges.update((u,v,s) for v,s in self.out[u])
        for v in [a,b]:
            edges.update((u,v,s) for u,s in self.inc[v] if u not in pair)
        swap=lambda n:b if n==a else a if n==b else n
        changed=Counter()
        for (u,v,s),count in edges.items():changed[swap(u),swap(v),s]+=count
        if changed!=edges:raise ValueError('incident multiset not invariant')
        return sum(edges.values())
