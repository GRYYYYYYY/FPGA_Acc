"""Privately owned graph/RC/compiled workspace and exclusive serial episodes.

This version admits only identical frozen episode inputs after the first run.
Different-placement rebinding is deliberately not admitted by this contract.
Every episode still runs original input proofs, state initialization and guards.
"""
import json
from pathlib import Path
from dataclasses import dataclass
from types import MappingProxyType
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints,Nodes
from load_design_routing_inputs_v2 import load as load_inputs
from compiled_criticality_tree_v1 import Graph
from native_price_buffer_store_v1 import Store
from mmc_model_lifetime_v2 import Model

@dataclass(frozen=True)
class FrozenNodes(Nodes):
    strings:tuple
    columns:object
    orders:tuple
    order_ids:object
    frozen:bool=True

def seal(nodes,fields,rc):
    copied={k:memoryview(v.tobytes()).cast(v.typecode) for k,v in fields.items()}
    f=MappingProxyType(copied)
    n=FrozenNodes(tuple(nodes.strings),MappingProxyType({k:memoryview(v.tobytes()).cast(v.format) for k,v in nodes.columns.items()}),tuple(tuple(x) for x in nodes.orders),memoryview(nodes.order_ids.tobytes()).cast(nodes.order_ids.format))
    rc.fields=f;rc.rc.fields=f
    if hasattr(rc.increments,'codes'):rc.increments.codes=memoryview(rc.increments.codes.tobytes()).cast(rc.increments.codes.format)
    return n,f,rc

class GraphLease:
    def __init__(self,core,token):self._core=core;self._token=token;self.closed=False
    def __getattr__(self,name):
        if self.closed:raise RuntimeError('closed episode graph')
        self._core._check(self._token)
        return getattr(self._core._backend,name)
    def close(self):self.closed=True

class Core:
    def __init__(self,*,loader=load_endpoints,input_loader=load_inputs,backend_factory=Graph,episode_factory=None):
        self._loader=loader;self._input_loader=input_loader;self._factory=backend_factory;self._episode_factory=episode_factory or Episode
        self._loaded=None;self._endpoint_key=None;self._base=None;self._backend=None;self._token=None;self._episode=None;self._bindings=None;self._signature=None;self.closed=False
        self.stats=dict(graph_loads=0,graph_reuses=0,backend_builds=0,backend_reuses=0,price_stores=0,episodes=0,releases=0)
    def _check(self,token):
        if self.closed or token is not self._token:raise RuntimeError('stale/closed design lease')
    def _load(self,token,endpoint):
        self._check(token);path=Path(endpoint).resolve();raw=path.read_bytes();ep=json.loads(raw)
        if self._endpoint_key is not None and self._endpoint_key!=(str(path),raw):raise ValueError('different endpoint snapshot not admitted')
        if not all(sha(x['path'])==x['sha256'] for x in ep['inputs'].values()):raise ValueError('endpoint input changed')
        if self._loaded is None:
            g,d,n,f,rc,_=self._loader(path);n,f,rc=seal(n,f,rc)
            if path.read_bytes()!=raw or sha(g)!=d:raise ValueError('graph load input changed')
            self._loaded=(g,d,n,f,rc);self._endpoint_key=(str(path),raw);self.stats['graph_loads']+=1
        else:
            g,d,n,f,rc=self._loaded
            if sha(g)!=d:raise ValueError('resident graph bytes changed')
            self.stats['graph_reuses']+=1
        return g,d,n,f,rc,ep['connections']
    def _inputs(self,token,*args):
        self._check(token);base,criticalities,bindings=self._input_loader(*args)
        if self._base is None:self._base=tuple(base)
        elif tuple(base)!=self._base:raise ValueError('different node-base not admitted')
        return self._base,criticalities,bindings
    def _store(self,token,fields,base):
        self._check(token)
        if fields is not self._loaded[3] or base is not self._base:raise ValueError('price input owner mismatch')
        self.stats['price_stores']+=1
        return Store(fields,base)
    def _graph(self,token,fields,increments,initial):
        self._check(token)
        if fields is not self._loaded[3] or increments is not self._loaded[4].increments:raise ValueError('compiled graph input owner mismatch')
        if self._backend is None:
            self._backend=self._factory(fields,increments,initial);self.stats['backend_builds']+=1
        else:
            if tuple(initial)!=self._backend.initial or self._backend.closed:raise ValueError('compiled graph domain changed')
            self._backend.total_stats=[0,0,0];self._backend.last_stats=None;self.stats['backend_reuses']+=1
        return GraphLease(self,token)
    def open(self,*args):
        if self.closed or self._token is not None:raise RuntimeError('design closed or episode already active')
        signature=tuple(str(Path(x).resolve()) if i!=5 else x for i,x in enumerate(args) if i!=1)
        if self._signature is not None and signature!=self._signature:raise ValueError('different episode input configuration not admitted')
        if self._bindings is not None and not all(sha(p)==h for p,h in self._bindings.items()):raise ValueError('frozen episode inputs changed')
        token=object();self._token=token
        try:
            m=self._episode_factory(*args,core=self,token=token)
            if self._bindings is not None and dict(m._bindings)!=self._bindings:raise ValueError('different episode proof bindings')
            self._bindings=dict(m._bindings);self._signature=signature;self._episode=m;self.stats['episodes']+=1
            return m
        except BaseException:
            if 'm' in locals():m.close()
            self._release(token);raise
    def _release(self,token):
        if token is self._token:self._token=None;self._episode=None;self.stats['releases']+=1
    def close(self):
        if self.closed:return
        if self._episode is not None:self._episode.close()
        if self._backend is not None:self._backend.close()
        self.closed=True

class Episode(Model):
    def __init__(self,*args,core,token):
        self._core=core;self._token=token
        hooks={'load_endpoints':lambda ep:core._load(token,ep),'load_design_inputs':lambda *x:core._inputs(token,*x),'Store':lambda f,b:core._store(token,f,b),'CriticalityGraph':lambda f,inc,initial:core._graph(token,f,inc,initial)}
        super().__init__(*args,overrides=hooks)
    def export(self,ticket):
        try:return super().export(ticket)
        finally:
            if self.phase in ['EXPORTED','CLOSED']:self._core._release(self._token)
    def close(self):
        try:super().close()
        finally:self._core._release(self._token)
