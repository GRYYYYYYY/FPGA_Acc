"""Immutable selection/serialization snapshot from an authenticated model CSR.

Caller supplies the completed model's graph/digest/nodes/fields. This is a serial
handoff, not a concurrent epoch service or an independent XML correctness audit.
Whole-file graph authentication remains mandatory on construction/validation.
"""
from array import array
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from pre_route_endpoints import sha
from prepared_csr import TYPES

@dataclass(frozen=True, slots=True)
class Node:
    capacity: int

@dataclass(frozen=True, slots=True)
class Edge:
    source: int
    sink: int
    switch_id: int

@dataclass(frozen=True, slots=True)
class EdgeTable:
    source: object
    sink: object
    switch: object
    def __len__(self):return len(self.source)
    def __getitem__(self,i):
        if type(i) is not int or not 0<=i<len(self):raise KeyError(i)
        return Edge(self.source[i],self.sink[i],self.switch[i])

@dataclass(frozen=True, slots=True)
class NativeEdges:
    table: EdgeTable
    def __len__(self):return len(self.table)
    def __getitem__(self,i):
        e=self.table[i];return e.source,e.sink,e.switch_id

@dataclass(frozen=True, slots=True)
class Graph:
    nodes: tuple
    edges: EdgeTable

@dataclass(frozen=True, slots=True)
class Snapshot:
    path: Path
    digest: str
    graph: Graph
    nodes: tuple
    edges: NativeEdges
    def validate(self,path,digest):
        if Path(path)!=self.path or digest!=self.digest or sha(path)!=digest:
            raise ValueError('graph identity changed')

def capture(path,digest,nodes,fields):
    path=Path(path)
    if sha(path)!=digest:raise ValueError('graph identity')
    n=len(nodes);m=len(fields['edge_ids']);rows=fields['row_offsets']
    if not n or len(fields['node_ids'])!=n or any(v!=i for i,v in enumerate(fields['node_ids'])):
        raise ValueError('original node identity')
    if len(rows)!=n+1 or rows[0]!=0 or rows[-1]!=m or any(a>b for a,b in zip(rows,rows[1:])):
        raise ValueError('CSR rows')
    if any(len(fields[k])!=m for k in ['dest_ranks','switch_ids']) or len(fields['capacities'])!=n:
        raise ValueError('column length')
    caps=tuple(fields['capacities']);locations=[]
    for i,node in enumerate(nodes):
        kind=node.get('type');loc=node.find('loc')
        if kind not in TYPES or loc is None or caps[i]<0 or int(node.get('capacity'))!=caps[i]:
            raise ValueError('node metadata/capacity')
        locations.append((kind,MappingProxyType(dict(loc.attrib))))
    sources=array('Q',[0])*m;sinks=array('Q',[0])*m;switches=array('Q',[0])*m;seen=bytearray(m)
    for u in range(n):
        for slot in range(rows[u],rows[u+1]):
            eid=fields['edge_ids'][slot];v=fields['dest_ranks'][slot];s=fields['switch_ids'][slot]
            if not 0<=eid<m or seen[eid] or not 0<=v<n or s<0:raise ValueError('original edge identity/domain')
            seen[eid]=1;sources[eid]=u;sinks[eid]=v;switches[eid]=s
    table=EdgeTable(*(memoryview(a.tobytes()).cast('Q') for a in [sources,sinks,switches]))
    if sha(path)!=digest:raise ValueError('graph changed during capture')
    return Snapshot(path,digest,Graph(tuple(Node(c) for c in caps),table),tuple(locations),NativeEdges(table))
