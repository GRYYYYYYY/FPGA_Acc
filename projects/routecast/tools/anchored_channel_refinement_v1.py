"""Necessary invariant for coupled channel-only automorphisms with fixed anchors.

Positive channels start with exact metadata colors; every other vertex has its
own fixed negative color. Directed weighted neighbor multisets refine colors.
Singleton channels rule out nonidentity permutations in this declared domain.
Non-singleton colors are not a certificate that any permutation is legal.
"""
from collections import defaultdict,Counter

def initial(metadata):
    lookup={};colors={}
    for n in sorted(metadata):
        key=metadata[n]
        if key not in lookup:lookup[key]=len(lookup)+1
        colors[n]=lookup[key]
    return colors

def step(colors,outgoing,incoming):
    lookup={};result={}
    for n in sorted(colors):
        out=tuple(sorted((colors.get(v,-v-1),s) for v,s in outgoing[n]))
        inc=tuple(sorted((colors.get(u,-u-1),s) for u,s in incoming[n]))
        key=(colors[n],out,inc)
        if key not in lookup:lookup[key]=len(lookup)+1
        result[n]=lookup[key]
    return result

def summary(colors):
    counts=Counter(colors.values());unresolved=[c for c in counts.values() if c>1]
    return {'classes':len(counts),'non_singleton_classes':len(unresolved),'unresolved_channels':sum(unresolved),'largest_class':max(counts.values(),default=0)}
