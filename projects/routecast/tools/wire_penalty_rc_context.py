"""Exact RC budgets with a fixed additive channel-length search cost."""
from fractions import Fraction as F
from persistent_rc_context import PersistentRCContext

class WirePenaltyRCContext(PersistentRCContext):
    def __init__(self, endpoint_path, weight_ns=F(1,100)):
        super().__init__(endpoint_path)
        if not isinstance(weight_ns,F) or weight_ns<0:
            raise ValueError('nonnegative exact Fraction wire weight required')
        unit=weight_ns*self.rc.scale/10**9
        if unit.denominator!=1:
            raise ValueError('wire weight not exactly representable at RC scale')
        self.weight_ns=weight_ns
        self.wire_lengths=[]
        for node in self.context[2]:
            loc=node.find('loc')
            if node.get('type')=='CHANX':length=int(loc.get('xhigh'))-int(loc.get('xlow'))+1
            elif node.get('type')=='CHANY':length=int(loc.get('yhigh'))-int(loc.get('ylow'))+1
            else:length=0
            if length<0:raise ValueError('negative channel span')
            self.wire_lengths.append(length)
        self.penalties=[int(unit)*self.wire_lengths[n] for n in self.rc.fields['dest_ranks']]
        costs=[v+p for v,p in zip(self.rc.increments,self.penalties)]
        if any(not 0<=v<(1<<64)-1 for v in costs):
            raise ValueError('wire cost exceeds uint64 non-sentinel range')
        for slot,cost in enumerate(costs):self.native.arrays[3][slot]=cost
    def set_history(self, history):
        staged={}
        for node,count in history.items():
            if type(node) is not int or not 0<=node<self.native.n or type(count) is not int or count<0:
                raise ValueError('history requires valid node and nonnegative integer count')
            if count:staged[node]=count
        updates=[]
        for node in self.history.keys()|staged.keys():
            if self.history.get(node,0)==staged.get(node,0):continue
            for slot in self.destination_slots.get(node,()):
                cost=self.rc.increments[slot]*(1+staged.get(node,0))+self.penalties[slot]
                if not 0<=cost<(1<<64)-1:raise ValueError('wire/history cost exceeds uint64 non-sentinel range')
                updates.append((slot,cost))
        for slot,cost in updates:self.native.arrays[3][slot]=cost
        self.history=staged
