"""CPU Pareto-label search minimizing native length under delay and crossing caps.

Capacities/policy are encoded in the immutable allowed mask. This primitive
has no tree sharing, hop limit, transactions or native STA acceptance.
"""
from heapq import heappop, heappush


def search(nodes, edges, allowed, native_length, source, sink, delay_budget,
           crossing_cost, crossing_budget, maximum_labels=2097152, suffix_delay=None):
    if delay_budget < 0 or crossing_budget < 0 or maximum_labels < 1:
        raise ValueError('invalid delay or label budget')
    if not (len(nodes) == len(allowed) == len(native_length)):
        raise ValueError('graph dimensions differ')
    if not (0 <= source < len(nodes) and 0 <= sink < len(nodes)):
        raise ValueError('invalid endpoint')
    if any(v < 0 for v in native_length):
        raise ValueError('negative native length')
    if suffix_delay is not None and len(suffix_delay) != len(nodes):
        raise ValueError('suffix dimensions differ')
    if not allowed[source] or not allowed[sink]:
        return dict(status='no_feasible_path',labels=0,expanded=0)
    if len(crossing_cost)!=len(edges) or any(v<0 for v in crossing_cost):
        raise ValueError('invalid crossing-cost vector')
    # Labels are (vertex, wire, delay, crossings, parent, incoming_edge).
    labels=[(source,0,0,0,-1,-1)];active={0};frontier={source:[0]}
    pending=[(0,0,0,0)];expanded=0
    while pending:
        wire, delay, used_crossings, index=heappop(pending)
        if index not in active:
            continue
        u=labels[index][0];expanded+=1
        if u == sink:
            path=[];edge_path=[];cursor=index
            while labels[cursor][4] != -1:
                node,_,_,_,parent,edge=labels[cursor]
                path.append(node);edge_path.append(edge);cursor=parent
            return dict(status='optimal_path',wire=wire,delay=delay,crossings=used_crossings,
                        path_nodes=[source]+list(reversed(path)),path_edges=list(reversed(edge_path)),
                        labels=len(labels),expanded=expanded)
        begin,size,*_=nodes[u]
        for edge_index in range(begin,begin+size):
            v,_,weight=edges[edge_index]
            if weight < 0:
                raise ValueError('negative edge delay')
            next_delay=delay+weight;next_wire=wire+native_length[v];next_cross=used_crossings+crossing_cost[edge_index]
            if not allowed[v] or next_delay>delay_budget or next_cross>crossing_budget:
                continue
            if suffix_delay is not None and next_delay+suffix_delay[v]>delay_budget:
                continue
            existing=frontier.get(v,[])
            if any(labels[j][1]<=next_wire and labels[j][2]<=next_delay and labels[j][3]<=next_cross for j in existing):
                continue
            # Exhaustion is distinct from a proof that no feasible path exists.
            if len(labels)>=maximum_labels:
                return dict(status='label_budget_exhausted',labels=len(labels),expanded=expanded)
            survivors=[]
            for j in existing:
                if next_wire<=labels[j][1] and next_delay<=labels[j][2] and next_cross<=labels[j][3]:
                    active.discard(j)
                else:
                    survivors.append(j)
            new_index=len(labels);labels.append((v,next_wire,next_delay,next_cross,index,edge_index))
            active.add(new_index);frontier[v]=survivors+[new_index]
            heappush(pending,(next_wire,next_delay,next_cross,new_index))
    return dict(status='no_feasible_path',labels=len(labels),expanded=expanded)
