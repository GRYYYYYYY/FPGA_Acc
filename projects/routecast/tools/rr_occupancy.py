"""Incremental node occupancy ledger for explicit RR connection paths.

Counts unique nets per node. Paths are candidates, not validated VPR route trees:
non-configurable closures and reconvergence legality are outside this ledger.
"""
from collections import Counter
from dataclasses import dataclass
from connection_golden import Result, UINT64_MAX, integer


@dataclass(frozen=True)
class RRConnection:
    net_id: int
    source: int
    sink: int
    edge_ids: tuple
    nodes: frozenset


class Occupancy:
    def __init__(self, graph):
        self.graph=graph
        self._states={}
        self._refs=Counter()
        self._occupancy=Counter()

    @property
    def states(self): return dict(self._states)

    @property
    def occupancy(self): return {nid:self._occupancy[nid] for nid in self.graph.nodes}

    def update(self, connection_id, epoch, net_id=None, source=None, sink=None, edge_ids=None, *, remove=False):
        if not integer(connection_id,0,UINT64_MAX) or not integer(epoch,1,UINT64_MAX) or type(remove) is not bool:
            return Result.INVALID
        previous=self._states.get(connection_id)
        if previous is not None and epoch<=previous[0]: return Result.STALE
        replacement=None
        if remove:
            if any(x is not None for x in (net_id,source,sink,edge_ids)): return Result.INVALID
        else:
            if (not integer(net_id,0,UINT64_MAX) or type(source) is not int or type(sink) is not int or
                source not in self.graph.nodes or sink not in self.graph.nodes or
                self.graph.nodes[source].type!='SOURCE' or self.graph.nodes[sink].type!='SINK' or
                not isinstance(edge_ids,(tuple,list))): return Result.INVALID
            current=source; nodes={source}; path=tuple(edge_ids)
            for eid in path:
                if not integer(eid,0,len(self.graph.edges)-1): return Result.INVALID
                edge=self.graph.edges[eid]
                if edge.source!=current or edge.sink in nodes: return Result.INVALID
                current=edge.sink; nodes.add(current)
            if current!=sink or any(self.graph.nodes[nid].capacity==0 for nid in nodes):
                return Result.INVALID
            # All active connections of a net must share one SOURCE.
            for cid,(_,conn) in self._states.items():
                if cid!=connection_id and conn is not None and conn.net_id==net_id and conn.source!=source:
                    return Result.INVALID
            replacement=RRConnection(net_id,source,sink,path,frozenset(nodes))
        delta=Counter()
        if previous is not None and previous[1] is not None:
            old=previous[1]
            for nid in old.nodes: delta[(old.net_id,nid)]-=1
        if replacement is not None:
            for nid in replacement.nodes: delta[(replacement.net_id,nid)]+=1
        for key,value in delta.items():
            old_count=self._refs[key]; new_count=old_count+value
            if new_count<0: raise AssertionError('reference underflow')
            self._occupancy[key[1]]+=int(new_count>0)-int(old_count>0)
            if new_count: self._refs[key]=new_count
            else: self._refs.pop(key,None)
        self._states[connection_id]=(epoch,replacement)
        return Result.COMMITTED

    def rebuild(self):
        nets={}
        for _,conn in self._states.values():
            if conn is not None: nets.setdefault(conn.net_id,set()).update(conn.nodes)
        totals=Counter(nid for used in nets.values() for nid in used)
        return {nid:totals[nid] for nid in self.graph.nodes}

    def overflow(self):
        return {nid:self._occupancy[nid]-node.capacity for nid,node in self.graph.nodes.items()
                if self._occupancy[nid]>node.capacity}
