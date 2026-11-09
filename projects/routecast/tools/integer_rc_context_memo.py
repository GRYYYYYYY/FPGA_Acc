"""Exact finite-lattice adapter, no RC quantization or float conversion."""
from math import lcm

class IntegerRC:
 def __init__(self,rc):
  self.rc=rc;self.fields=rc.fields
  # Only actual graph arc class/switch pairs and node initial states matter.
  scale=1
  for n in range(len(self.fields['node_ids'])):
   r,c=rc.node(n);scale=lcm(scale,(r*c/2).denominator)
  for slot in range(len(self.fields['edge_ids'])):scale=lcm(scale,rc.increment(slot).denominator)
  self.scale=scale;encoded={};self.increments=[]
  for i in range(len(self.fields['edge_ids'])):
   value=rc.increment(i);key=(value.numerator,value.denominator)
   if key not in encoded:encoded[key]=self.encode(value)
   self.increments.append(encoded[key])
 def encode(self,value):
  product=value*self.scale
  if product.denominator!=1:raise ValueError('value outside exact lattice')
  return product.numerator
 def node(self,n):return self.rc.node(n)
 def initial(self,n):
  r,c=self.rc.node(n);return self.encode(r*c/2)
 def increment(self,slot):return self.increments[slot]
 def path(self,source,sink,edges):return self.encode(self.rc.path(source,sink,edges))
