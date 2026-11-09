"""Exact lattice construction once per used electrical class/pair, no quantization."""
from math import lcm
from integer_rc_context import IntegerRC as Original
class IntegerRC(Original):
 def __init__(self,rc):
  self.rc=rc;self.fields=rc.fields
  used=set(rc.node_classes);initials={c:rc.classes[c][0]*rc.classes[c][1]/2 for c in used}
  pairs={};keys=[]
  for i in range(len(self.fields['edge_ids'])):
   key=(rc.node_classes[self.fields['dest_ranks'][i]],self.fields['switch_ids'][i]);keys.append(key)
   if key not in pairs:pairs[key]=rc.increment(i)
  self.scale=lcm(1,*(v.denominator for v in initials.values()),*(v.denominator for v in pairs.values()))
  encoded={k:self.encode(v) for k,v in pairs.items()};self.increments=[encoded[k] for k in keys];self.initial_by_class={k:self.encode(v) for k,v in initials.items()}
 def initial(self,n):
  if type(n) is not int or not 0<=n<len(self.rc.node_classes):raise ValueError('invalid raw node')
  return self.initial_by_class[self.rc.node_classes[n]]
