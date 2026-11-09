"""Exact integer maximum-weight closure with an explicit flow/cut certificate."""
from collections import deque


def solve(weights,implications):
    nodes=sorted(weights)
    if any(type(n) is not int or type(weights[n]) is not int for n in nodes):raise ValueError('integer nodes and weights required')
    index={n:i for i,n in enumerate(nodes)};edges=sorted(set(implications))
    if any(u not in index or v not in index for u,v in edges):raise ValueError('unknown implication endpoint')
    n=len(nodes);source=n;sink=n+1;adj=[[] for _ in range(n+2)];original=[]
    def add(u,v,capacity):
        slot=len(adj[u]);back=len(adj[v]);adj[u].append([v,back,capacity]);adj[v].append([u,slot,0]);original.append((u,v,capacity,slot))
    infinity=sum(abs(w) for w in weights.values())+1
    for node in nodes:
        w=weights[node]
        if w>0:add(source,index[node],w)
        elif w<0:add(index[node],sink,-w)
    for u,v in edges:
        if u!=v:add(index[u],index[v],infinity)
    total=0
    while True:
        level=[-1]*(n+2);level[source]=0;queue=deque([source])
        while queue:
            u=queue.popleft()
            for v,back,capacity in adj[u]:
                if capacity>0 and level[v]<0:level[v]=level[u]+1;queue.append(v)
        if level[sink]<0:break
        cursor=[0]*(n+2)
        while True:
            vertices=[source];path=[];amount=0
            while vertices:
                u=vertices[-1]
                if u==sink:
                    amount=min(adj[a][slot][2] for a,slot in path)
                    for a,slot in path:
                        v,back,capacity=adj[a][slot];adj[a][slot][2]-=amount;adj[v][back][2]+=amount
                    break
                while cursor[u]<len(adj[u]):
                    v,back,capacity=adj[u][cursor[u]]
                    if capacity>0 and level[v]==level[u]+1:break
                    cursor[u]+=1
                if cursor[u]==len(adj[u]):
                    level[u]=-1;vertices.pop()
                    if path:path.pop()
                else:path.append((u,cursor[u]));vertices.append(adj[u][cursor[u]][0])
            if not amount:break
            total+=amount
    reachable={source};pending=[source]
    while pending:
        u=pending.pop()
        for v,back,capacity in adj[u]:
            if capacity>0 and v not in reachable:reachable.add(v);pending.append(v)
    assert sink not in reachable
    selected=tuple(node for node in nodes if index[node] in reachable)
    return dict(nodes=nodes,selected=selected,objective=sum(weights[n] for n in selected),source=source,sink=sink,flow_value=total,
                infinity=infinity,source_side=sorted(reachable),arcs=[dict(source=u,target=v,capacity=c,flow=c-adj[u][slot][2]) for u,v,c,slot in original])


def verify(weights,implications,certificate):
    """Check primal flow and equal-capacity feasible cut; no solver execution."""
    nodes=sorted(weights);index={n:i for i,n in enumerate(nodes)};n=len(nodes);source=n;sink=n+1
    assert certificate['nodes']==nodes and certificate['source']==source and certificate['sink']==sink
    infinity=sum(abs(w) for w in weights.values())+1;assert certificate['infinity']==infinity
    expected={}
    for node,w in weights.items():
        if w>0:expected[source,index[node]]=w
        elif w<0:expected[index[node],sink]=-w
    for u,v in set(implications):
        if u!=v:expected[index[u],index[v]]=infinity
    arcs=certificate['arcs'];assert len(arcs)==len(expected);seen=set();balance=[0]*(n+2)
    for arc in arcs:
        u,v,c,f=[arc[k] for k in ['source','target','capacity','flow']];assert all(type(x) is int for x in [u,v,c,f])
        assert (u,v) not in seen and expected[u,v]==c and 0<=f<=c;seen.add((u,v));balance[u]-=f;balance[v]+=f
    assert seen==set(expected);value=certificate['flow_value'];assert all(balance[i]==0 for i in range(n)) and balance[source]==-value and balance[sink]==value
    side=set(certificate['source_side']);assert source in side and sink not in side and side<=set(range(n+2))
    cut=sum(c for (u,v),c in expected.items() if u in side and v not in side);assert cut==value
    selected={node for node in nodes if index[node] in side};assert selected==set(certificate['selected'])
    assert all(u not in selected or v in selected for u,v in implications)
    objective=sum(weights[n] for n in selected);assert objective==certificate['objective']==sum(max(0,w) for w in weights.values())-cut
    return objective
