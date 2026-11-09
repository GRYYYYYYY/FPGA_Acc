"""Exact original-path budgets without allocating a full-graph edge-weight vector."""
from fractions import Fraction
from path_rc import PathRC,State

def budgets(graph,connections):
    rc=PathRC(graph)
    if any(not buffered or internal for buffered,_,_,internal in rc.switches.values()):
        raise ValueError('requires all switches buffered with zero Cinternal')
    result={}
    for row in connections:
        cid=row['connection_id'];source=row['source'];sink=row['sink'];path=row['physical_edge_ids']
        if type(cid) is not int or cid in result:raise ValueError('invalid or duplicate connection ID')
        if type(source) is not int or source not in rc.nodes or type(sink) is not int or sink not in rc.nodes:
            raise ValueError('unknown endpoint')
        if path is None:raise ValueError('missing original path')
        resistance,capacitance=rc.nodes[source]
        state=State(resistance,resistance*capacitance/2)
        current=source;seen={source}
        for eid in path:
            if type(eid) is not int or not 0<=eid<len(graph.edges):raise ValueError('invalid edge ID')
            edge=graph.edges[eid]
            if edge.source!=current or edge.sink in seen:raise ValueError('discontinuous or cyclic original path')
            state=rc.step(state,eid);current=edge.sink;seen.add(current)
        if current!=sink:raise ValueError('wrong terminal')
        if not isinstance(state.delay,Fraction):raise ValueError('nonexact budget')
        result[cid]=state.delay
    return result
