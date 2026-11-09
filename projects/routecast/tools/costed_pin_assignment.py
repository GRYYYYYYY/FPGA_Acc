"""Exact additive min-cost injective assignment; costs are caller supplied."""
from pin_assignment import assign

def assign_costed(costs):
    for options in costs.values():
        if any(type(c) is not int or c < 0 for c in options.values()):
            raise ValueError('cost must be a nonnegative integer')
    feasible = assign({r:list(options) for r,options in costs.items()})
    if feasible['status'] != 'matched':
        return {**feasible,'total_cost':None}
    requests=sorted(costs);pins=sorted({p for options in costs.values() for p in options})
    # Residual min-cost flow; Bellman-Ford handles negative reverse arcs exactly.
    sink=1+len(requests)+len(pins);nodes=sink+1;edges=[]
    def add(a,b,c):
        idx=len(edges);edges.extend([[a,b,1,c],[b,a,0,-c]])
        return idx
    request_nodes={r:i+1 for i,r in enumerate(requests)}
    pin_nodes={p:1+len(requests)+i for i,p in enumerate(pins)}
    assignment_edges={}
    for r in requests:
        add(0,request_nodes[r],0)
        for p in sorted(costs[r]):assignment_edges[r,p]=add(request_nodes[r],pin_nodes[p],costs[r][p])
    for p in pins:add(pin_nodes[p],sink,0)
    for _ in requests:
        dist=[None]*nodes;parent=[None]*nodes;dist[0]=0
        for _pass in range(nodes-1):
            changed=False
            for idx,(a,b,capacity,cost) in enumerate(edges):
                if capacity and dist[a] is not None and (dist[b] is None or dist[a]+cost<dist[b]):
                    dist[b]=dist[a]+cost;parent[b]=idx;changed=True
            if not changed:break
        if dist[sink] is None:raise AssertionError('feasible matching lost')
        cursor=sink;seen=set()
        while cursor!=0:
            if cursor in seen or parent[cursor] is None:raise AssertionError('bad residual predecessor')
            seen.add(cursor);idx=parent[cursor];edges[idx][2]-=1;edges[idx^1][2]+=1;cursor=edges[idx][0]
    selected={r:list(p) for (r,p),idx in assignment_edges.items() if edges[idx][2]==0}
    assert len(selected)==len(requests) and len({tuple(p) for p in selected.values()})==len(requests)
    return {'status':'matched','assignment':selected,'hall_witness':None,
            'total_cost':sum(costs[r][tuple(p)] for r,p in selected.items()),
            'scope':'optimal supplied additive cost only; no joint channel, route-tree or timing feasibility'}
