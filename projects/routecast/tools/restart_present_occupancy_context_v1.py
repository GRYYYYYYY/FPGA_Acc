"""Fixed prospectively registered [0,1/2] present schedule, unchanged owner tickets."""
from cached_multiplicative_occupancy_context_v1 import Context as Original
class Context(Original):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.round_index=-1;self.numerator=0;self.denominator=1
 def price(self,node,count):
  base=self.base[node]*(1+self.history[node]);m=max(0,count-self.caps[node]+1)
  return base+self.numerator*base*m//self.denominator+self.weight*self.spans[node]-self.base[node]
 def start_round(self,history,weight,ledger):
  if self.round_index>=1:raise RuntimeError('only two registered rounds allowed')
  self.round_index+=1;self.numerator,self.denominator=((0,1),(1,2))[self.round_index]
  return super().start_round(history,weight,ledger)
