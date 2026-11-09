"""Serial immutable decoded seed inputs, authenticated by whole-byte equality.

Two latest file snapshots only. Budget covers retained raw bytes, not decoded RSS.
Positive per-connection pin bindings are scoped to the exact input generation
and immutable graph. No route paths, occupancy, or model epochs are cached here.
"""
import json
from pathlib import Path
from types import MappingProxyType
from collections import defaultdict

def freeze(v):
    if isinstance(v,dict):return MappingProxyType({k:freeze(x) for k,x in v.items()})
    if isinstance(v,list):return tuple(freeze(x) for x in v)
    return v

class Inputs:
    def __init__(self,max_raw_bytes=64*1024*1024):
        self.max_raw_bytes=max_raw_bytes;self._ep=None;self._identity=None;self._bindings={};self.generation=0
        self.stats=dict(endpoint_hits=0,endpoint_misses=0,identity_hits=0,identity_misses=0,binding_hits=0,binding_misses=0)
    def load(self,endpoint_path,identity_path):
        ep_path=str(Path(endpoint_path).absolute());ipath=str(Path(identity_path).absolute())
        epraw=Path(endpoint_path).read_bytes();iraw=Path(identity_path).read_bytes()
        ep_hit=self._ep is not None and self._ep[:2]==(ep_path,epraw)
        identity_hit=self._identity is not None and self._identity[:2]==(ipath,iraw)
        self.stats['endpoint_hits' if ep_hit else 'endpoint_misses']+=1
        self.stats['identity_hits' if identity_hit else 'identity_misses']+=1
        if ep_hit:ep,queries=self._ep[2:]
        else:
            ep=freeze(json.loads(epraw));queries=MappingProxyType({q['connection_id']:q for q in ep['connections']})
        if identity_hit:nets,indexes=self._identity[2:]
        else:
            nets=freeze({r['name']:r for r in map(json.loads,iraw.splitlines())});indexes={}
            for name,native in nets.items():
                sources=[];sinks=defaultdict(list)
                for pin in native['pins']:
                    if pin['index']==0:sources.append(pin)
                    elif pin['index']>0:sinks[tuple(pin[k] for k in ('x','y','layer','class'))].append(pin)
                indexes[name]=(tuple(sources),MappingProxyType({k:tuple(v) for k,v in sinks.items()}))
            indexes=MappingProxyType(indexes)
        if not ep_hit or not identity_hit:
            self.generation+=1;self._bindings={}
        if len(epraw)+len(iraw)<=self.max_raw_bytes:
            self._ep=(ep_path,epraw,ep,queries);self._identity=(ipath,iraw,nets,indexes)
        else:
            self._ep=self._identity=None
        return ep,queries,nets,indexes,(ep_path,epraw,ipath,iraw)
    def finish(self,token):
        ep,raw,identity,iraw=token
        if Path(ep).read_bytes()!=raw or Path(identity).read_bytes()!=iraw:
            self._ep=self._identity=None;self._bindings={};self.generation+=1
            raise ValueError('input bytes changed during serialization')
    def key(self,inventory,q):
        return (self.generation,str(inventory.path),inventory.digest,q['connection_id'],q['net_id'],q['source'],q['sink'])
    def binding(self,key):
        value=self._bindings.get(key);self.stats['binding_hits' if value is not None else 'binding_misses']+=1
        return value
    def remember(self,key,value):self._bindings[key]=MappingProxyType(dict(value))
