"""Owned immutable compact model columns and original-ID edges for serial handoff.

Full graph authentication remains charged. No mutable model references survive.
This transport is not an independent XML audit or a concurrent epoch service.
"""
from array import array
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping
from pre_route_endpoints import sha
from prepared_csr import TYPES
from compact_stream_rc_endpoint_context_v1 import Nodes as ModelNodes
from model_inventory_snapshot_v1 import Node,EdgeTable,NativeEdges,Graph,Snapshot

@dataclass(frozen=True, slots=True, eq=False)
class Location(Mapping):
    columns: object
    strings: tuple
    index: int
    def __getitem__(self,key):
        col=self.columns.get(key);code=0 if col is None else col[self.index]
        if not code:raise KeyError(key)
        return self.strings[code]
    def __iter__(self):return (key for key,col in self.columns.items() if col[self.index])
    def __len__(self):return sum(bool(col[self.index]) for col in self.columns.values())

@dataclass(frozen=True, slots=True)
class Locations:
    types: object
    columns: object
    strings: tuple
    def __len__(self):return len(self.types)
    def __getitem__(self,i):
        if type(i) is not int or not 0<=i<len(self):raise KeyError(i)
        return self.strings[self.types[i]],Location(self.columns,self.strings,i)

@dataclass(frozen=True, slots=True)
class Capacities:
    values: object
    def __len__(self):return len(self.values)
    def __getitem__(self,i):
        if type(i) is not int or not 0<=i<len(self):raise KeyError(i)
        return Node(self.values[i])

def capture(path,digest,nodes,fields):
    path=Path(path)
    if sha(path)!=digest:raise ValueError('graph identity')
    if not isinstance(nodes,ModelNodes) or not nodes.frozen:raise ValueError('frozen compact model nodes required')
    n=len(nodes);m=len(fields['edge_ids']);rows=fields['row_offsets']
    if not n or len(fields['node_ids'])!=n or any(v!=i for i,v in enumerate(fields['node_ids'])):raise ValueError('original node identity')
    if len(rows)!=n+1 or rows[0]!=0 or rows[-1]!=m or any(a>b for a,b in zip(rows,rows[1:])):raise ValueError('CSR rows')
    if any(len(fields[k])!=m for k in ['dest_ranks','switch_ids']) or len(fields['capacities'])!=n:raise ValueError('column length')
    # Copy backing bytes, not merely a read-only view of a mutable exporter.
    strings=tuple(nodes.strings);orders=tuple(tuple(order) for order in nodes.orders)
    order_ids=memoryview(nodes.order_ids.tobytes()).cast('I')
    columns=MappingProxyType({k:memoryview(v.tobytes()).cast('I') for k,v in nodes.columns.items()})
    if not strings or strings[0] is not None or any(not isinstance(s,str) for s in strings[1:]):raise ValueError('metadata strings')
    if len(order_ids)!=n or any(i>=len(orders) or 'loc' not in orders[i] for i in order_ids):raise ValueError('node child metadata')
    if any(len(col)!=n or max(col,default=0)>=len(strings) for col in columns.values()):raise ValueError('metadata column domain')
    types=columns.get(('node','type'));capcol=columns.get(('node','capacity'))
    if types is None or capcol is None:raise ValueError('missing node metadata')
    allowed={i for i,s in enumerate(strings) if s in TYPES}
    if any(v not in allowed for v in types):raise ValueError('node type')
    caps=array('Q',fields['capacities'])
    if any(not code or int(strings[code])!=cap for code,cap in zip(capcol,caps)):raise ValueError('node capacity')
    sources=array('Q',[0])*m;sinks=array('Q',[0])*m;switches=array('Q',[0])*m;seen=bytearray(m)
    for u in range(n):
        for slot in range(rows[u],rows[u+1]):
            eid=fields['edge_ids'][slot];v=fields['dest_ranks'][slot];s=fields['switch_ids'][slot]
            if not 0<=eid<m or seen[eid] or not 0<=v<n or s<0:raise ValueError('original edge identity/domain')
            seen[eid]=1;sources[eid]=u;sinks[eid]=v;switches[eid]=s
    table=EdgeTable(*(memoryview(a.tobytes()).cast('Q') for a in [sources,sinks,switches]))
    loccols=MappingProxyType({key:col for (tag,key),col in columns.items() if tag=='loc'})
    if not loccols:raise ValueError('location metadata')
    if sha(path)!=digest:raise ValueError('graph changed during capture')
    return Snapshot(path,digest,Graph(Capacities(memoryview(caps.tobytes()).cast('Q')),table),Locations(types,loccols,strings),NativeEdges(table))
