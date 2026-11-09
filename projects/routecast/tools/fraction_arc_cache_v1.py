"""Immutable independent electrical context; cache exact Fraction arc costs only."""
from types import MappingProxyType
from buffered_rc_node_classes import arc_delay
class FractionArcCache:
    def __init__(self,classes,switches):
        self.classes=tuple(tuple(x) for x in classes)
        self.switches=MappingProxyType({k:tuple(v) for k,v in switches.items()})
        self.values={}
        self.hits=0
    def __call__(self,node_class,switch_id):
        key=(node_class,switch_id)
        if key in self.values:
            self.hits+=1
            return self.values[key]
        result=arc_delay(self.classes,self.switches,node_class,switch_id)
        self.values[key]=result
        return result
