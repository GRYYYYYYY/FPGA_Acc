"""Exact 2-SAT for forbidden binary owner-state pairs, with checkable UNSAT paths."""
from collections import deque

def solve(variables,forbidden):
    names=sorted(set(variables));index={n:i for i,n in enumerate(names)};size=2*len(names);adj=[[] for _ in range(size)];rev=[[] for _ in range(size)]
    def literal(v):
        n,b=v
        if n not in index or type(b) is not bool:raise ValueError('owner literal domain')
        return 2*index[n]+int(b)
    for k,clause in enumerate(forbidden):
        if len(clause) not in [1,2]:raise ValueError('unit or pair required')
        a=literal(clause[0]);b=literal(clause[-1]);arcs=[(a,b^1)] if len(clause)==1 else [(a,b^1),(b,a^1)]
        for u,v in arcs:adj[u].append((v,k));rev[v].append(u)
    seen=bytearray(size);order=[]
    for root in range(size):
        if seen[root]:continue
        seen[root]=1;stack=[(root,0)]
        while stack:
            u,i=stack[-1]
            if i==len(adj[u]):order.append(u);stack.pop();continue
            stack[-1]=(u,i+1);v=adj[u][i][0]
            if not seen[v]:seen[v]=1;stack.append((v,0))
    component=[-1]*size;count=0
    for root in reversed(order):
        if component[root]>=0:continue
        component[root]=count;todo=[root]
        while todo:
            u=todo.pop()
            for v in rev[u]:
                if component[v]<0:component[v]=count;todo.append(v)
        count+=1
    def path(a,b):
        parents={a:None};todo=deque([a])
        while todo and b not in parents:
            u=todo.popleft()
            for v,k in adj[u]:
                if component[v]==component[a] and v not in parents:parents[v]=(u,k);todo.append(v)
        assert b in parents;steps=[];u=b
        while parents[u] is not None:
            p,k=parents[u];steps.append({'from':[names[p//2],bool(p%2)],'to':[names[u//2],bool(u%2)],'clause':k});u=p
        return list(reversed(steps))
    for i,n in enumerate(names):
        if component[2*i]==component[2*i+1]:return {'satisfiable':False,'conflict_NET':n,'false_to_true':path(2*i,2*i+1),'true_to_false':path(2*i+1,2*i)}
    assignment={n:component[2*i+1]>component[2*i] for i,n in enumerate(names)}
    assert all(not all(assignment[n]==b for n,b in c) for c in forbidden)
    return {'satisfiable':True,'assignment':assignment,'SCCs':count}
