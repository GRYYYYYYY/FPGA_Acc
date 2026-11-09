"""Necessary new-NET-support lower bound for fixed complete A/B candidate banks."""
from functools import lru_cache

def minimum_cover(edges,max_states=100000):
    edges=tuple(sorted({tuple(sorted(e)) for e in edges}))
    if any(len(e)!=2 or e[0]==e[1] for e in edges):raise ValueError('simple owner conflict edges required')
    calls=0
    @lru_cache(None)
    def solve(es):
        nonlocal calls
        calls+=1
        if calls>max_states:raise RuntimeError('exact cover state budget exceeded')
        if not es:return ()
        a,b=es[0];choices=[]
        for n in [a,b]:choices.append(tuple(sorted((n,)+solve(tuple(e for e in es if n not in e)))))
        return min(choices,key=lambda c:(len(c),c))
    cover=solve(edges)
    assert all(set(e)&set(cover) for e in edges)
    return {'minimum_departures':len(cover),'cover':list(cover),'states':calls}

def components(edges):
    adj={}
    for a,b in edges:adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
    seen=set();out=[]
    for root in sorted(adj):
        if root in seen:continue
        todo=[root];seen.add(root);nodes=[]
        while todo:
            n=todo.pop();nodes.append(n)
            for v in adj[n]:
                if v not in seen:seen.add(v);todo.append(v)
        members=set(nodes);out.append((sorted(nodes),sorted(e for e in edges if e[0] in members)))
    return out
