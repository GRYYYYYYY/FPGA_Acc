"""Caller-owned NET union reduces only incremental wire cost, never RC delay."""
from wire_penalty_rc_context_cached_tree import WirePenaltyRCContext

class OwnerUnionWireRCContext(WirePenaltyRCContext):
    def __init__(self, endpoint_path, **kwargs):
        super().__init__(endpoint_path, **kwargs)
        self.wire_owner_union=frozenset()
    def _cost(self, slot, history, owner):
        node=self.rc.fields['dest_ranks'][slot]
        return self.rc.increments[slot]*(1+history.get(node,0))+(0 if node in owner else self.penalties[slot])
    def _publish(self, nodes, history, owner):
        updates=[]
        for node in nodes:
            for slot in self.destination_slots.get(node,()):
                cost=self._cost(slot,history,owner)
                if not 0<=cost<(1<<64)-1:
                    raise ValueError('owner/history cost exceeds uint64 non-sentinel range')
                updates.append((slot,cost))
        for slot,cost in updates:self.native.arrays[3][slot]=cost
    def set_wire_owner_union(self, nodes):
        staged=set()
        for node in nodes:
            if type(node) is not int or not 0<=node<self.native.n:
                raise ValueError('invalid owner union node')
            staged.add(node)
        owner=frozenset(staged)
        self._publish(self.wire_owner_union^owner,self.history,owner)
        self.wire_owner_union=owner
    def set_history(self, history):
        staged={}
        for node,count in history.items():
            if type(node) is not int or not 0<=node<self.native.n or type(count) is not int or count<0:
                raise ValueError('history requires valid node and nonnegative integer count')
            if count:staged[node]=count
        changed={n for n in self.history.keys()|staged.keys() if self.history.get(n,0)!=staged.get(n,0)}
        self._publish(changed,staged,self.wire_owner_union)
        self.history=staged
    def restore_wire_state(self, history, nodes):
        owner=set()
        for node in nodes:
            if type(node) is not int or not 0<=node<self.native.n:
                raise ValueError('invalid owner union node')
            owner.add(node)
        owner=frozenset(owner);staged={}
        for node,count in history.items():
            if type(node) is not int or not 0<=node<self.native.n or type(count) is not int or count<0:
                raise ValueError('invalid history')
            if count:staged[node]=count
        changed=(self.wire_owner_union^owner)|{n for n in self.history.keys()|staged.keys() if self.history.get(n,0)!=staged.get(n,0)}
        self._publish(changed,staged,owner)
        self.wire_owner_union=owner;self.history=staged
    def reset(self):
        # Clear both in one publication, with no overflowing intermediate cost.
        self.restore_wire_state({},())
        self.native.set_other({})
