"""Immutable complete physical-edge permutation inverse without Python dicts."""
from array import array
from collections.abc import Mapping

class EdgeSlots(Mapping):
    def __init__(self,edge_ids):
        self.n=len(edge_ids)
        if all(type(eid) is int and eid==i for i,eid in enumerate(edge_ids)):
            self.inverse=None
        else:
            missing=2**64-1;values=array('Q',[missing])*self.n
            for slot,eid in enumerate(edge_ids):
                if type(eid) is not int or not 0<=eid<self.n or values[eid]!=missing:
                    raise ValueError('physical edge IDs must be a complete unique permutation')
                values[eid]=slot
            self.inverse=memoryview(values.tobytes()).cast('Q')
    def __len__(self):return self.n
    def __iter__(self):return iter(range(self.n))
    def __getitem__(self,eid):
        if type(eid) is not int or not 0<=eid<self.n:raise KeyError(eid)
        return eid if self.inverse is None else self.inverse[eid]
