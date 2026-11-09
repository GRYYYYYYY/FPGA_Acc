"""Binary complete-tree choice dependencies on singly owned capacity-one resources.

For an eligible resource with A-owner v and B-owner u, mixed occupancy is
1[x_u=B] + 1[x_v=A]. It exceeds one exactly when x_u=B and x_v=A.
No promise is made for resources overused in either full bank or capacity>1.
"""
from collections import defaultdict


def build(nodes, owners_a, owners_b, capacities):
    nodes=frozenset(nodes)
    if any(type(n) is not int or n<0 for n in nodes):raise ValueError('NET domain')
    witnesses=defaultdict(list);eligible=[]
    for resource in sorted(set(owners_a)|set(owners_b)):
        a,b=set(owners_a.get(resource,())),set(owners_b.get(resource,()))
        if not a<=nodes or not b<=nodes:raise ValueError('owner outside NET domain')
        if capacities[resource]!=1 or len(a)!=1 or len(b)!=1:continue
        eligible.append(resource);v=next(iter(a));u=next(iter(b))
        if u!=v:witnesses[u,v].append(resource)
    return dict(nodes=tuple(sorted(nodes)),eligible_resources=tuple(eligible),
                edges=tuple(sorted(witnesses)),witnesses={edge:tuple(witnesses[edge]) for edge in sorted(witnesses)})


def close(graph,seeds):
    chosen=set(seeds)
    if not chosen<=set(graph['nodes']):raise ValueError('seed outside NET domain')
    outgoing=defaultdict(list)
    for u,v in graph['edges']:outgoing[u].append(v)
    pending=list(sorted(chosen))
    while pending:
        u=pending.pop()
        for v in outgoing[u]:
            if v not in chosen:chosen.add(v);pending.append(v)
    return frozenset(chosen)


def components(graph):
    forward=defaultdict(list);reverse=defaultdict(list)
    for u,v in graph['edges']:forward[u].append(v);reverse[v].append(u)
    seen=set();order=[]
    for root in graph['nodes']:
        if root in seen:continue
        pending=[(root,False)]
        while pending:
            u,exit_node=pending.pop()
            if exit_node:order.append(u);continue
            if u in seen:continue
            seen.add(u);pending.append((u,True))
            pending.extend((v,False) for v in reversed(forward[u]) if v not in seen)
    assigned=set();groups=[]
    for root in reversed(order):
        if root in assigned:continue
        group=[];pending=[root];assigned.add(root)
        while pending:
            u=pending.pop();group.append(u)
            for v in reverse[u]:
                if v not in assigned:assigned.add(v);pending.append(v)
        groups.append(tuple(sorted(group)))
    return tuple(sorted(groups,key=lambda group:group[0]))
