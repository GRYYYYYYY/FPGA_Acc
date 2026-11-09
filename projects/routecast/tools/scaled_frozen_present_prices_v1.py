"""Immutable native snapshot prices for exact integer search; no ledger mutation."""
from fractions import Fraction
class Prices:
 def __init__(self,bases,acc,occupancy,capacities,owned,present,static=None):
  if type(present) is not Fraction or present<0:raise ValueError('rational present required')
  self.base=tuple(bases);self.acc=tuple(acc);self.occ=tuple(occupancy);self.cap=tuple(capacities)
  self.static=tuple(static) if static is not None else (0,)*len(self.base)
  if not len(self.base)==len(self.acc)==len(self.occ)==len(self.cap)==len(self.static):raise ValueError('domains')
  if any(type(x) is not int or x<0 for seq in (self.base,self.occ,self.cap,self.static) for x in seq) or any(type(x) is not int or x<1 for x in self.acc):raise ValueError('snapshot integer domain')
  self.owned=frozenset(owned);self.denominator=present.denominator;self.numerator=present.numerator
  if any(type(n) is not int or not 0<=n<len(self.base) or self.occ[n]==0 for n in self.owned):raise ValueError('invalid old owner')
 def get(self,node,default=0):
  if type(node) is not int or not 0<=node<len(self.base):raise ValueError('node domain')
  if self.occ[node] and self.cap[node]==0:raise ValueError('owned zero capacity')
  others=self.occ[node]-int(node in self.owned);pressure=max(0,others-self.cap[node]+1)
  return self.base[node]*self.acc[node]*(self.denominator+pressure*self.numerator)+self.static[node]*self.denominator
 def scale_raw(self,value):
  if type(value) is not int or value<0:raise ValueError('raw integer')
  return value*self.denominator
