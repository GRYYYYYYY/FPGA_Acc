"""Graph-defined input-pin class pools and incremental distinct-net demand.

This is a capacity relaxation. It does not assert that all class pins are
reachable from each source, solve pin assignment, or remove real IPIN contention.
Physical pin identity is (SINK class, ptc), not RR side/facet node ID.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from connection_golden import Result, UINT64_MAX, integer


@dataclass(frozen=True)
class PinPool:
    sink: int
    capacity: int
    physical_pins: object


def build_pools(graph):
    members=defaultdict(lambda:defaultdict(set)); owner={}
    for edge in graph.edges:
        if graph.nodes[edge.source].type!='IPIN' or graph.nodes[edge.sink].type!='SINK':continue
        pin=graph.nodes[edge.source]
        if pin.capacity!=1:raise ValueError('non-unit IPIN capacity unsupported')
        if edge.source in owner and owner[edge.source]!=edge.sink:raise ValueError('IPIN has multiple SINK classes')
        owner[edge.source]=edge.sink
        members[edge.sink][int(dict(pin.location)['ptc'])].add(edge.source)
    pools={}
    for nid,node in graph.nodes.items():
        if node.type!='SINK':continue
        pins=members[nid]
        if len(pins)!=node.capacity:raise ValueError(f'SINK {nid} physical pin count differs from class capacity')
        pools[nid]=PinPool(nid,node.capacity,MappingProxyType({p:tuple(sorted(ids)) for p,ids in sorted(pins.items())}))
    if {n for n,node in graph.nodes.items() if node.type=='IPIN'}!=set(owner):
        raise ValueError('IPIN without direct SINK class unsupported')
    return MappingProxyType(pools),MappingProxyType(owner)


class PinDemand:
    def __init__(self,pools):
        self.pools=pools;self._states={};self._refs=Counter();self._demand=Counter()

    @property
    def states(self):return dict(self._states)

    @property
    def demand(self):return {sid:self._demand[sid] for sid in self.pools}

    def update(self,connection_id,epoch,net_id=None,sink=None,*,remove=False):
        if not integer(connection_id,0,UINT64_MAX) or not integer(epoch,1,UINT64_MAX) or type(remove) is not bool:
            return Result.INVALID
        old=self._states.get(connection_id)
        if old is not None and epoch<=old[0]:return Result.STALE
        replacement=None
        if remove:
            if net_id is not None or sink is not None:return Result.INVALID
        else:
            if not integer(net_id,0,UINT64_MAX) or type(sink) is not int or sink not in self.pools or self.pools[sink].capacity==0:
                return Result.INVALID
            replacement=(net_id,sink)
        delta=Counter()
        if old is not None and old[1] is not None:delta[old[1]]-=1
        if replacement is not None:delta[replacement]+=1
        for key,value in delta.items():
            before=self._refs[key];after=before+value
            if after<0:raise AssertionError('pool reference underflow')
            self._demand[key[1]]+=int(after>0)-int(before>0)
            if after:self._refs[key]=after
            else:self._refs.pop(key,None)
        self._states[connection_id]=(epoch,replacement)
        return Result.COMMITTED

    def pressure(self,sink):
        pool=self.pools[sink]
        return Fraction(self._demand[sink],pool.capacity) if pool.capacity else None

    def physical_pin_expectation(self,sink):
        # Uniform relaxation only: no direction/connection reachability claim.
        pool=self.pools[sink]
        if not pool.capacity:return {}
        value=self.pressure(sink)
        result={pin:value for pin in pool.physical_pins}
        if sum(result.values())!=self._demand[sink]:raise AssertionError('fractional demand not conserved')
        return result

    def rebuild(self):
        active=defaultdict(set)
        for _,key in self._states.values():
            if key is not None:active[key[1]].add(key[0])
        return {sid:len(active[sid]) for sid in self.pools}
