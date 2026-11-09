"""Private implicit-CSR variant; path edge indices refer to original CSR.

Greedy ordering, caps and label decisions are retained.
"""
from implicit_tree_budget_search import search


def repair(nodes, edges, allowed, native_length, node_die, source, tasks,
           crossing_budget, maximum_labels=2097152):
    """Build locally; return no published state, even on partial failure.

    Task dictionaries contain id, sink, delay_budget and max_hops. Previously
    selected tree parents remain fixed. Each shared crossing edge is charged
    once per net, not once per connection. No global Steiner optimality claim.
    """
    if len(node_die)!=len(nodes) or crossing_budget<0:
        raise ValueError('invalid die metadata or crossing budget')
    parent={};tree_nodes={source};steps=[]
    def crossings(mapping):
        return sum(node_die[v]!=node_die[u] for v,u in mapping.items())
    for task in tasks:
        old_cross=crossings(parent)
        incremental=[0 if v in tree_nodes else length for v,length in enumerate(native_length)]
        answer=search(nodes,edges,allowed,incremental,source,task['sink'],
                      task['delay_budget'],node_die,parent,crossing_budget-old_cross,
                      maximum_labels=maximum_labels)
        steps.append(dict(task=task['id'],before_crossings=old_cross,search=answer))
        if answer['status']!='optimal_path':
            return dict(complete=False,status=answer['status'],steps=steps,
                        private_parent=parent,published=False)
        path=answer['path_nodes']
        if len(set(path))!=len(path) or len(path)-1>task['max_hops']:
            return dict(complete=False,status='path_guard_failed',steps=steps,
                        private_parent=parent,published=False)
        previous_wire=sum(native_length[v] for v in parent)
        for u,v in zip(path,path[1:]):
            assert v not in parent or parent[v]==u
            parent[v]=u;tree_nodes.add(v)
        assert crossings(parent)==old_cross+answer['crossings']<=crossing_budget
        assert sum(native_length[v] for v in parent)==previous_wire+answer['wire']
    paths={}
    for task in tasks:
        path=[];v=task['sink']
        while v!=source:
            path.append(v);v=parent[v]
        paths[task['id']]=list(reversed(path))
    return dict(complete=True,status='private_tree_complete',parent=parent,paths=paths,
                crossings=crossings(parent),wire=sum(native_length[v] for v in parent),
                steps=steps,published=False)
