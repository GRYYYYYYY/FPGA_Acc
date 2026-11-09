"""Half damping in integer demand units, with explicit upward rounding.

ceil((old+new)/2) leaves a one-unit demand at one when new demand is zero.
This is a quantified rounding bias, not a convergence guarantee.
"""
from collections.abc import Mapping

def half_background(graph,old,new):
    for values in (old,new):
        if not isinstance(values,Mapping):raise ValueError('background must be a mapping')
        for n,v in values.items():
            if type(n) is not int or n not in graph.nodes or type(v) is not int or v<0:raise ValueError('invalid background demand')
    result={}
    for n in set(old)|set(new):
        value=(old.get(n,0)+new.get(n,0)+1)//2
        if value:result[n]=value
    return result
