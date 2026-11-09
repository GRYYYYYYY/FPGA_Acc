"""Exact integer lattice from distinct used node/arc electrical classes."""
from math import lcm
from integer_rc_context_memo import IntegerRC as Reference
class IntegerRC:
 encode=Reference.encode
 node=Reference.node
 initial=Reference.initial
 increment=Reference.increment
 path=Reference.path
 def __init__(self,rc):
  self.rc=rc;self.fields=rc.fields;scale=1
  # Only used classes/pairs contribute denominators, exactly as per-node/per-arc enumeration.
  for klass in set(rc.node_classes):
   r,c=rc.classes[klass];scale=lcm(scale,(r*c/2).denominator)
  representatives={}
  for slot,(node,switch) in enumerate(zip(self.fields['dest_ranks'],self.fields['switch_ids'])):
   representatives[(rc.node_classes[node],switch)]=slot
  values={key:rc.increment(slot) for key,slot in representatives.items()}
  for value in values.values():scale=lcm(scale,value.denominator)
  self.scale=scale;encoded={key:self.encode(value) for key,value in values.items()}
  self.increments=[encoded[(rc.node_classes[node],switch)] for node,switch in zip(self.fields['dest_ranks'],self.fields['switch_ids'])]
