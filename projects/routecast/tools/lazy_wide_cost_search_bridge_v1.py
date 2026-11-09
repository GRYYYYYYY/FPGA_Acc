"""Allocate certified exact graph engines only when that engine is queried.

Every prepared price buffer exists immediately, including sparse patches before
the first query. Engine allocation cannot change prices, dispatch, ties or paths.
"""
from wide_cost_search_bridge_v1 import Forward as EngineForward, Bidirectional as EngineBidi, Words, LIMIT

class Deferred:
    def __init__(self,fields,rc,binary,engine):
        self.fields,self.rc,self.binary,self.engine=fields,rc,binary,engine
        self.n=len(fields['capacities']);self.initial=tuple(rc.initial(u) for u in range(self.n))
        self.maxinc=max(rc.increments,default=0);self.maxinitial=max(self.initial,default=0)
        self.price=Words([0]*self.n);self.weight=0;self.prepared=False;self.closed=False;self.backend=None
    def prepare(self,prices,weight):
        if self.closed:raise RuntimeError('closed search')
        values=tuple(prices.get(u,0) for u in range(self.n))
        if type(weight) is not int or not 0<=weight<LIMIT or any(type(v) is not int or not 0<=v<LIMIT for v in values):
            raise ValueError('invalid prices or weight')
        if 2*self.n*(self.maxinc+weight*max(values,default=0))+self.maxinitial>=LIMIT:
            raise ValueError('cost envelope exceeded')
        if self.backend is not None:
            self.backend.prepare(prices,weight);self.price=self.backend.price
        else:self.price=Words(values)
        self.weight=weight;self.prepared=True
    def search(self,*args):
        if self.closed or not self.prepared:raise RuntimeError('closed or unprepared search')
        if self.backend is None:
            backend=self.engine(self.fields,self.rc,self.binary)
            owner=self
            class Prices:
                def get(self,node,default=0):return owner.price[node]
            try:backend.prepare(Prices(),self.weight)
            except Exception:backend.close();raise
            self.backend=backend;self.price=backend.price
        return self.backend.search(*args)
    def close(self):
        if self.backend is not None:self.backend.close()
        self.closed=True

class Search:
    def __init__(self,fields,rc,binary):
        self.fields,self.rc=fields,rc
        self.forward=Deferred(fields,rc,binary,EngineForward)
        self.bidirectional=Deferred(fields,rc,binary,EngineBidi)
    def prepare(self,prices,weight):
        self.forward.prepare(prices,weight);self.bidirectional.prepare(prices,weight)
    def search(self,source,sinks):
        targets=set(sinks)
        if len(targets)!=1:return self.forward.search(source,targets)
        sink=next(iter(targets));answer=self.bidirectional.search(source,sink)
        if answer is None:return {},{},set()
        u=source;parents={}
        for slot in answer['slots']:
            v=self.fields['dest_ranks'][slot]
            assert self.fields['row_offsets'][u]<=slot<self.fields['row_offsets'][u+1]
            assert v not in parents and v!=source
            parents[v]=(u,slot);u=v
        assert u==sink
        return {source:self.rc.initial(source),sink:answer['raw']},parents,{sink}
    def close(self):
        for name in ['forward','bidirectional']:
            if hasattr(self,name):getattr(self,name).close()
    def __del__(self):self.close()

def intern_objective_increments(raw,targets,base):
    """Equal exact integer sums share one immutable Python object."""
    values={}
    def value(cost,target):
        key=(cost,base[target])
        if key not in values:values[key]=cost+base[target]
        return values[key]
    return tuple(value(cost,target) for cost,target in zip(raw,targets))
