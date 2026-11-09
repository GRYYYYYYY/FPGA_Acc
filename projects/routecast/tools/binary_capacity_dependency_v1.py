"""Exact two-bank capacity1 clauses; higher capacities must be bank-invariant.
Pure candidate-bank analysis, not routing, objective optimization or prediction.
"""
from collections import defaultdict,deque
from itertools import combinations

def components(graph):
    seen=set();order=[]
    for root in range(len(graph)):
        if root in seen:continue
        seen.add(root);stack=[(root,iter(graph[root]))]
        while stack:
            u,it=stack[-1]
            try:v=next(it)
            except StopIteration:order.append(u);stack.pop();continue
            if v not in seen:seen.add(v);stack.append((v,iter(graph[v])))
    reverse=[[] for _ in graph]
    for u,vs in enumerate(graph):
        for v in vs:reverse[v].append(u)
    labels=[-1]*len(graph);groups=[]
    for root in reversed(order):
        if labels[root]>=0:continue
        index=len(groups);group=[];labels[root]=index;stack=[root]
        while stack:
            u=stack.pop();group.append(u)
            for v in reverse[u]:
                if labels[v]<0:labels[v]=index;stack.append(v)
        groups.append(sorted(group))
    return labels,groups,reverse

def analyse(bankA,bankB,capacities,forbiddenB):
    nets=sorted(bankA)
    if set(nets)!=set(bankB) or not set(forbiddenB)<=set(nets):raise ValueError('NET bank domain')
    index={net:i for i,net in enumerate(nets)};a=defaultdict(set);b=defaultdict(set)
    for net in nets:
        for node in bankA[net]:a[node].add(net)
        for node in bankB[net]:b[node].add(net)
    graph=[set() for _ in range(2*len(nets))];reasons={};clauses=[];dependencies=[set() for _ in nets];constant_nodes=0;unit_nodes=0
    def add(x,y,reason):
        clauses.append((x,y));graph[x^1].add(y);graph[y^1].add(x);reasons.setdefault((x^1,y),reason);reasons.setdefault((y^1,x),reason)
    for node in sorted(a.keys()|b.keys()):
        if type(node) is not int or not 0<=node<len(capacities):raise ValueError('node domain')
        cap=capacities[node]
        if type(cap) is not int or cap<=0:raise ValueError('nonpositive capacity')
        if len(b[node])>cap:raise ValueError('bankB not capacity legal')
        if cap!=1:
            if a[node]!=b[node]:raise ValueError('nonunit capacity changes are unsupported')
            if len(a[node])>cap:raise ValueError('constant capacity overflow')
            constant_nodes+=1;continue
        unit_nodes+=1
        for i,j in combinations(sorted(a[node]),2):add(2*index[i]+1,2*index[j]+1,dict(kind='two_A_owners',node=node,NETs=[i,j]))
        for i in sorted(b[node]):
            for j in sorted(a[node]-{i}):
                dependencies[index[i]].add(index[j]);add(2*index[i],2*index[j]+1,dict(kind='B_requires_A_release',node=node,requester=i,owner=j))
    for net in sorted(forbiddenB):add(2*index[net],2*index[net],dict(kind='budget_forbids_B',net_id=net))
    graph=[sorted(v) for v in graph];labels,groups,rev=components(graph);conflicts=[i for i in range(len(nets)) if labels[2*i]==labels[2*i+1]];sat=not conflicts;assignment=None;certificate=None
    if sat:
        assignment={net:labels[2*i+1]>labels[2*i] for i,net in enumerate(nets)}
        assert all(assignment[nets[x//2]]==bool(x%2) or assignment[nets[y//2]]==bool(y%2) for x,y in clauses)
        occupancy=defaultdict(int)
        for net in nets:
            assert net not in forbiddenB or not assignment[net]
            for node in (bankB[net] if assignment[net] else bankA[net]):occupancy[node]+=1
        assert all(count<=capacities[node] for node,count in occupancy.items())
    else:
        variable=conflicts[0]
        def witness(source,target):
            parents={source:None};queue=deque([source])
            while queue and target not in parents:
                u=queue.popleft()
                for v in graph[u]:
                    if labels[v]==labels[source] and v not in parents:parents[v]=u;queue.append(v)
            assert target in parents;path=[];v=target
            while v!=source:
                u=parents[v];path.append(dict(source_literal=u,target_literal=v,reason=reasons[u,v]));v=u
            return path[::-1]
        certificate=dict(net_id=nets[variable],false_implies_true=witness(2*variable,2*variable+1),true_implies_false=witness(2*variable+1,2*variable))
    dep=[sorted(v) for v in dependencies];dl,dg,dr=components(dep);blocked={index[n] for n in forbiddenB};queue=deque(blocked)
    while queue:
        v=queue.popleft()
        for u in dr[v]:
            if u not in blocked:blocked.add(u);queue.append(u)
    return dict(satisfiable=sat,assignment_B=assignment,unsat_certificate=certificate,nets=nets,clauses=len(clauses),implication_edges=sum(map(len,graph)),constant_nonunit_resources=constant_nodes,unit_resources=unit_nodes,dependency_edges=sum(map(len,dep)),budget_forbidden_B=len(forbiddenB),budget_allowed_B_blocked_by_release_dependencies=len(blocked)-len(forbiddenB),dependency_SCC_sizes=sorted((len(g) for g in dg),reverse=True),nontrivial_dependency_SCCs=sum(len(g)>1 for g in dg),unblocked_nontrivial_dependency_SCCs=sum(len(g)>1 and not any(n in blocked for n in g) for g in dg),blocked_B_NETs=sorted(nets[i] for i in blocked),dependency_edges_NETs=[[nets[i],nets[j]] for i,vs in enumerate(dep) for j in vs])
