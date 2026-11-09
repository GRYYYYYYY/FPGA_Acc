"""Whole-NET pre-release snapshot algebra; not native connection-router parity."""
import struct,math
from dataclasses import dataclass
from collections import Counter
from types import MappingProxyType
PHASE='post_route_accumulated_cost_and_timing_update__pre_dynamic_BB_update_and_pres_advance'
def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]
def word(value):return struct.unpack('<I',struct.pack('<f',value))[0]
@dataclass(frozen=True,init=False)
class Snapshot:
 identity:tuple
 capacities:object
 occupancy:object
 owners:object
 pres_bits:int
 pres:float
 def __init__(self,identity,capacities,occupancy,owners,pres_bits,*,release_stage='not_applied'):
  if release_stage!='not_applied':raise ValueError('virtual owner release must not already be applied')
  if not identity or identity[-1]!=PHASE:raise ValueError('wrong observation phase')
  cap=dict(capacities);occ=dict(occupancy);own={n:frozenset(nodes) for n,nodes in owners.items()}
  if any(type(n) is not int or n<0 or type(c) is not int or c<=0 for n,c in cap.items()):raise ValueError('capacity domain')
  if set(occ)!=set(cap) or any(type(c) is not int or c<0 for c in occ.values()):raise ValueError('occupancy domain')
  if any(type(n) is not int or n<0 or not nodes<=cap.keys() for n,nodes in own.items()):raise ValueError('owner domain')
  counts=Counter(node for nodes in own.values() for node in nodes)
  if any(occ[n]!=counts[n] for n in cap):raise ValueError('uniqueNET owner/count mismatch')
  if type(pres_bits) is not int or not 0<=pres_bits<2**32:raise ValueError('present bits domain')
  pres=struct.unpack('<f',struct.pack('<I',pres_bits))[0]
  if not math.isfinite(pres) or pres<0:raise ValueError('present factor domain')
  for name,value in [('identity',tuple(identity)),('capacities',MappingProxyType(cap)),('occupancy',MappingProxyType(occ)),('owners',MappingProxyType(own)),('pres_bits',pres_bits),('pres',pres)]:object.__setattr__(self,name,value)
 def view(self,net,expected_identity):
  if tuple(expected_identity)!=self.identity:raise ValueError('wrong snapshot identity')
  if net not in self.owners:raise ValueError('unknown/ignored NET')
  return View(self,net)
@dataclass(frozen=True)
class View:
 snapshot:Snapshot
 net:int
 def multiplier_bits(self,node):
  s=self.snapshot
  if node not in s.capacities:raise ValueError('node outside CHANNEL universe')
  others=s.occupancy[node]-int(node in s.owners[self.net]);capacity=s.capacities[node]
  if others<0:raise ValueError('negative released occupancy')
  # Pinned native scalar expression: float product, double 1.+product, float result.
  return word(f32(1.0+f32(s.pres*(others+1-capacity))) if others>=capacity else 1.0)
