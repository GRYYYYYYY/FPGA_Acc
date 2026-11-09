"""Sparse Pareto delay search with a hard incremental crossing budget."""
from heapq import heappop,heappush

def search(adjacency,allowed,source,sink,fixed_parent,crossing_budget,maximum_labels=262144,delay_budget=None):
    """adjacency yields (destination,delay,incremental_crossing_charge).

    Minimize (additive delay,hops) with a hard crossing cap within delay_budget under immutable occupancy/parent guards.
    Existing same-net edges may have zero incremental crossing charge.
    Labels exhausted is not proof of infeasibility.
    """
    if crossing_budget<0 or maximum_labels<1 or (delay_budget is not None and delay_budget<0):raise ValueError('Invalid budget')
    if not allowed(source) or not allowed(sink):return {'status':'no_feasible_path','labels':0,'expanded':0}
    labels=[(source,0,0,0,-1)];frontier={source:[0]};active={0};queue=[(0,0,0,0)];expanded=0
    while queue:
        delay,hops,_,index=heappop(queue)
        if index not in active:continue
        u,used,_,_,previous=labels[index];expanded+=1
        if u==sink:
            path=[];cursor=index
            while cursor!=-1:path.append(labels[cursor][0]);cursor=labels[cursor][4]
            path.reverse();assert len(path)==len(set(path))
            return {'status':'optimal_bounded_delay_path','delay':delay,'hops':hops,'crossings':used,'path_nodes':path,'labels':len(labels),'expanded':expanded}
        for v,weight,charge in adjacency(u):
            if weight<0 or charge<0:raise ValueError('Negative edge cost')
            crossed=used+charge
            if crossed>crossing_budget or v==source or not allowed(v) or (v in fixed_parent and fixed_parent[v]!=u):continue
            cost=(delay+weight,hops+1)
            if delay_budget is not None and cost[0]>delay_budget:continue
            old=frontier.get(v,[])
            if any(labels[j][1]<=crossed and (labels[j][2],labels[j][3])<=cost for j in old):continue
            if len(labels)>=maximum_labels:return {'status':'label_budget_exhausted','labels':len(labels),'expanded':expanded}
            keep=[]
            for j in old:
                if crossed<=labels[j][1] and cost<=(labels[j][2],labels[j][3]):active.discard(j)
                else:keep.append(j)
            k=len(labels);labels.append((v,crossed,*cost,index));active.add(k);frontier[v]=keep+[k];heappush(queue,(*cost,crossed,k))
    return {'status':'no_feasible_path','labels':len(labels),'expanded':expanded}
