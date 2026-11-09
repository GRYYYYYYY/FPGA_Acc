"""Bounded sparse CPU delay search with immutable capacity and tree-parent guards."""
from heapq import heappop,heappush

def search(adjacency,allowed,source,sink,fixed_parent,maximum_expanded=262144):
    """Dijkstra by additive delay then hops, excluding occupied foreign nodes.

    adjacency(node) yields (destination, nonnegative delay). Existing same-net
    parent relations are immutable; capacity is encoded by allowed(node).
    A budget stop is not a proof of infeasibility. No native timing guarantee.
    """
    if maximum_expanded<1:raise ValueError('Invalid expansion budget')
    if not allowed(source) or not allowed(sink):
        return {'status':'no_feasible_path','expanded':0}
    dist={source:(0,0)};predecessor={};pending=[(0,0,source)];expanded=0
    while pending:
        delay,hops,u=heappop(pending)
        if dist.get(u)!=(delay,hops):continue
        if expanded>=maximum_expanded:
            return {'status':'expansion_budget_exhausted','expanded':expanded}
        expanded+=1
        if u==sink:
            path=[u]
            while u!=source:u=predecessor[u];path.append(u)
            return {'status':'optimal_additive_delay_path','delay':delay,
                    'hops':hops,'path_nodes':list(reversed(path)),'expanded':expanded}
        for v,weight in adjacency(u):
            if weight<0:raise ValueError('Negative edge delay')
            if v==source or not allowed(v) or (v in fixed_parent and fixed_parent[v]!=u):continue
            cost=(delay+weight,hops+1)
            if cost<dist.get(v,(float('inf'),float('inf'))):
                dist[v]=cost;predecessor[v]=u;heappush(pending,(*cost,v))
    return {'status':'no_feasible_path','expanded':expanded}
