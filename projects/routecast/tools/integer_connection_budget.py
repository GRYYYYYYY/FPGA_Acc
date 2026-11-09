"""Exact integer lattice envelope caps; arbitrary precision, no quantization."""
from fractions import Fraction as F
from math import lcm


class IntegerConnectionBudget:
    def __init__(self, dag, *, scale=None, extra_values=()):
        values = list(dag.budgets.values()) + list(extra_values)
        values += [offset for node in dag.order for _,offset,_ in dag.incoming[node]]
        if scale is None:
            scale = lcm(*(F(v).denominator for v in values))
        if type(scale) is not int or scale < 1:
            raise ValueError('positive exact lattice scale required')
        self.scale = scale
        self.order = tuple(dag.order)
        self.sinks = tuple(dag.sinks)
        self.budgets = {k:self.encode(v) for k,v in dag.budgets.items()}
        self.incoming = {n:tuple((u,self.encode(offset),cid) for u,offset,cid in dag.incoming[n]) for n in self.order}
        for value in extra_values:
            self.encode(value)

    def encode(self, value):
        if isinstance(value,(bool,float)):
            raise ValueError('exact rational required')
        encoded = F(value)*self.scale
        if encoded.denominator != 1:
            raise ValueError('value outside declared lattice')
        return encoded.numerator

    def update(self, changes):
        staged = {}
        for cid,value in changes.items():
            cid = str(cid)
            if cid not in self.budgets or cid in staged:
                raise ValueError('unknown or duplicate connection')
            encoded = self.encode(value)
            if encoded < 0:
                raise ValueError('negative delay')
            staged[cid] = encoded
        self.budgets.update(staged)

    def cap(self, connection_id, target_ns):
        cid = str(connection_id)
        if cid not in self.budgets:
            raise ValueError('unknown connection')
        target = self.encode(target_ns)
        if target < 0:
            raise ValueError('negative target')
        envelopes = {}
        for node in self.order:
            terms = {0:0}
            for source,offset,edge_cid in self.incoming[node]:
                repeat = int(edge_cid==cid)
                fixed = offset + (self.budgets[edge_cid] if edge_cid is not None and not repeat else 0)
                for count,base in envelopes[source].items():
                    k = count+repeat
                    value = base+fixed
                    if k not in terms or value>terms[k]:terms[k]=value
            envelopes[node] = terms
        numerator = denominator = None
        maximum = 0
        for node in self.sinks:
            for count,base in envelopes[node].items():
                maximum = max(maximum,count)
                if base>target:
                    return dict(feasible=False,cap_ns=None,reason='ZERO_DELAY_STILL_EXCEEDS_TARGET')
                if count:
                    bound = target-base
                    if numerator is None or bound*denominator<numerator*count:
                        numerator,denominator = bound,count
        return dict(feasible=True,cap_ns=F(numerator,denominator*self.scale) if numerator is not None else None,
                    reason='BOUNDED' if numerator is not None else 'NO_SINK_DEPENDENCY',maximum_repetitions=maximum)
