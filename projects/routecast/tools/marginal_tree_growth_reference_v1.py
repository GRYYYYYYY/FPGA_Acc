"""Deterministic greedy rooted tree growth, not global Steiner optimization.

Inputs are original node/edge IDs. Existing tree vertices are attachment seeds;
their prefix objective is sunk, but their raw delay prefix remains charged.
Growth cannot re-enter/reparent any existing vertex. Budgets are checked after
each minimum incremental-cost branch: failure rejects the entire candidate.
"""
import heapq


def grow(source, ordered_sinks, adjacency, increments, capacities, prices,
         weight, initial, budgets):
    parent={};raw={source:initial};paths={source:()};owned={source}
    records=[];branches=[]
    for sink in ordered_sinks:
        if sink not in owned:
            # All tree nodes can attach. SINKs naturally have no outgoing arcs;
            # graph legality, including zero capacity, stays in the adjacency.
            cost={n:0 for n in owned};dist={n:raw[n] for n in owned}
            prev={};queue=[(0,n) for n in sorted(owned)];heapq.heapify(queue)
            settled=set()
            while queue:
                value,u=heapq.heappop(queue)
                if value!=cost[u] or u in settled:continue
                settled.add(u)
                if u==sink:break
                for eid,v in adjacency.get(u,()):
                    if capacities.get(v,0)<=0 or v in owned:continue
                    candidate=value+increments[eid]+weight*prices.get(v,0)
                    if candidate<cost.get(v,float('inf')):
                        cost[v]=candidate;dist[v]=dist[u]+increments[eid]
                        prev[v]=(u,eid);heapq.heappush(queue,(candidate,v))
            if sink not in settled:
                return dict(status='RETAIN_OLD_TREE_UNREACHABLE',failed_sink=sink)
            if dist[sink]>budgets[sink]:
                return dict(status='RETAIN_OLD_TREE_BUDGET',failed_sink=sink,
                            delay=dist[sink],budget=budgets[sink])
            extension=[];u=sink
            while u not in owned:
                p,eid=prev[u];extension.append((p,u,eid));u=p
            attachment=u;extension.reverse()
            for p,u,eid in extension:
                assert p in owned and u not in owned
                parent[u]=(p,eid);raw[u]=raw[p]+increments[eid]
                paths[u]=paths[p]+(eid,);owned.add(u)
            branches.append(dict(sink=sink,attachment=attachment,
                                 incremental_cost=cost[sink],new_edges=[e for _,_,e in extension]))
        if raw[sink]>budgets[sink]:
            return dict(status='RETAIN_OLD_TREE_BUDGET',failed_sink=sink,
                        delay=raw[sink],budget=budgets[sink])
        records.append(dict(sink=sink,edges=list(paths[sink]),delay=raw[sink]))
    return dict(status='CANDIDATE',records=records,branches=branches,
                parent=parent,raw=raw,owned=sorted(owned))
