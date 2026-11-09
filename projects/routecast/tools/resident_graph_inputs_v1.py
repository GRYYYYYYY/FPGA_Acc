"""Reuse sealed graph data; always reauthenticate files and reload endpoints."""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from pre_route_endpoints import sha


@dataclass(frozen=True, slots=True)
class Element:
    tag: str
    attrib: object
    children: tuple
    def get(self,key,default=None):return self.attrib.get(key,default)
    def find(self,path):
        head,sep,tail=path.partition('/')
        child=next((c for c in self.children if c.tag==head),None)
        return child.find(tail) if child is not None and sep else child


def seal(element):
    return Element(element.tag,MappingProxyType(dict(element.attrib)),tuple(seal(c) for c in element))


@dataclass(frozen=True, slots=True)
class Electrical:
    scale: int
    increments: tuple
    initials: tuple
    _reference: object
    def initial(self,node):
        if type(node) is not int or not 0<=node<len(self.initials):raise ValueError('node domain')
        return self.initials[node]
    def increment(self,slot):return self.increments[slot]
    def path(self,source,sink,edges):return self._reference.path(source,sink,edges)


class ResidentGraphInputs:
    def __init__(self, original):
        self.original=original;self.cache={};self.stats=dict(requests=0,hits=0,misses=0)
    def __call__(self, endpoint_path):
        self.stats['requests']+=1
        endpoint=json.loads(Path(endpoint_path).read_text())
        graph=Path(endpoint['inputs']['graph']['path'])
        raw=graph.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest!=endpoint['graph_sha256'] or digest!=endpoint['inputs']['graph']['sha256']:
            raise ValueError('graph bytes changed')
        for name,spec in endpoint['inputs'].items():
            if name!='graph' and sha(spec['path'])!=spec['sha256']:raise ValueError('endpoint input changed')
        key=(str(graph.absolute()),digest)
        if key not in self.cache:
            path,checked,nodes,fields,rc,_=self.original(endpoint_path)
            if checked!=digest or Path(path).absolute()!=graph.absolute() or graph.read_bytes()!=raw:
                raise ValueError('graph changed during initialization')
            sealed_fields=MappingProxyType({k:tuple(v) for k,v in fields.items()})
            electrical=Electrical(rc.scale,tuple(rc.increments),tuple(rc.initial(i) for i in range(len(nodes))),rc)
            self.cache[key]=(raw,tuple(seal(n) for n in nodes),sealed_fields,electrical)
            self.stats['misses']+=1
        else:self.stats['hits']+=1
        saved,nodes,fields,rc=self.cache[key]
        if saved!=raw:raise ValueError('graph snapshot differs')
        # Queries are freshly decoded per call. No ledger/history/epoch is cached.
        return graph,digest,nodes,fields,rc,endpoint['connections']
