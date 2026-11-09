"""Exact serial price storage without unused search engines or graph copies.

Compatible with the existing multiplicative Context and compiled NativePrices.
No path search or resource-cost approximation is implemented here.
"""
from types import SimpleNamespace
from wide_cost_search_bridge_v2 import Words


class Store:
    def __init__(self,fields,node_base):
        self.fields={'capacities':tuple(fields['capacities'])}
        self.base=tuple(node_base);self.n=len(self.base)
        if self.n!=len(self.fields['capacities']) or not self.n:
            raise ValueError('price store domain')
        if any(type(v) is not int or not 0<=v<2**128 for v in self.base):
            raise ValueError('base outside price domain')
        if any(type(v) is not int or v<0 for v in self.fields['capacities']):
            raise ValueError('capacity domain')
        self.closed=False;self.prepared=False
        self.backends=[None,SimpleNamespace(forward=SimpleNamespace(price=None))]
    def prepare(self,prices,weight,*,structural=True,price_ceiling=None):
        if self.closed:raise RuntimeError('closed price store')
        if type(weight) is not int or weight!=1 or structural is not True:
            raise ValueError('price-only store requires unit structural pricing')
        if type(price_ceiling) is not int or not 0<=price_ceiling<2**128:
            raise ValueError('invalid price ceiling')
        values=[prices.get(n,0) for n in range(self.n)]
        if any(type(v) is not int or not 0<=v<=price_ceiling for v in values):
            raise ValueError('price exceeds ceiling')
        buffer=Words(values)
        # All inputs and allocations complete before replacing owned state.
        self.prices=values;self.backends[1].forward.price=buffer
        self.price_ceiling=price_ceiling;self.weight=weight;self.structural=True;self.prepared=True
    def patch_prices(self,changes):
        if self.closed or not self.prepared:raise RuntimeError('closed or unprepared price store')
        updates=dict(changes)
        for node,value in updates.items():
            if (type(node) is not int or not 0<=node<self.n or type(value) is not int
                or not 0<=value<=self.price_ceiling):raise ValueError('invalid sparse price patch')
        # Serial, same guarantees as the original price patcher: no interruption
        # or concurrent-search atomicity claim. No invalid-input partial patch.
        buffer=self.backends[1].forward.price
        for node,value in updates.items():buffer[node]=value;self.prices[node]=value
    def close(self):
        self.closed=True
        self.backends[1].forward.price=None
        self.prices=[]
