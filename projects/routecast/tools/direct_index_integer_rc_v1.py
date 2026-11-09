"""Exact integer path evaluation with authenticated CSR edge slots; no float arithmetic."""
from class_cached_integer_rc_v1 import IntegerRC as Base
class IntegerRC(Base):
 def __init__(self,rc):
  super().__init__(rc)
  self.edge_slots={eid:slot for slot,eid in enumerate(self.fields['edge_ids'])}
  if len(self.edge_slots)!=len(self.fields['edge_ids']):raise ValueError('unique physical edge IDs required')
 def path(self,source,sink,edges):
  delay=self.initial(source);self.rc.node(sink);current=source;seen={source};f=self.fields
  for eid in edges:
   if type(eid) is not int or eid<0:raise ValueError('invalid raw edge ID')
   slot=self.edge_slots.get(eid)
   if slot is None or not f['row_offsets'][current]<=slot<f['row_offsets'][current+1]:raise ValueError('discontinuous or ambiguous raw edge')
   current=f['dest_ranks'][slot]
   if current in seen:raise ValueError('cyclic path')
   seen.add(current);delay+=self.increments[slot]
  if current!=sink:raise ValueError('wrong terminal')
  return delay
