"""Pressure resolution experiment; original RR topology and RC stay intact."""
from collections import defaultdict
class PressurePool:
 def __init__(self,nodes,mode):
  if mode not in ('within_polarity','across_polarity'):raise ValueError('unknown mode')
  self.size=len(nodes);self.groups=[];groups=defaultdict(list)
  for nid,node in enumerate(nodes):
   if int(node.get('id'))!=nid:raise ValueError('original contiguous node IDs required')
   if node.get('type') not in ('CHANX','CHANY') or int(node.get('capacity'))<=0:continue
   loc=node.find('loc');seg=node.find('segment');timing=node.find('timing');direction=node.get('direction')
   if loc is None or direction not in ('INC_DIR','DEC_DIR','BI_DIR','NO_DIR'):raise ValueError('invalid original channel metadata')
   key=(node.get('type'),int(node.get('capacity')),tuple(loc.get(k,'0') for k in ('xlow','xhigh','ylow','yhigh','layer')),tuple(sorted(seg.attrib.items())) if seg is not None else (),tuple(sorted(timing.attrib.items())) if timing is not None else ())
   if mode=='within_polarity':key=(*key,direction)
   groups[key].append(nid)
  self.groups=[tuple(group) for group in groups.values()]
 def project(self,prices):
  if any(not isinstance(n,int) or not 0<=n<self.size or not isinstance(v,int) or v<0 for n,v in prices.items()):raise ValueError('invalid original prices')
  projected=dict(prices)
  for group in self.groups:
   # Integer ceiling of the complete group's mean, including zero-price nodes.
   value=(sum(prices.get(n,0) for n in group)+len(group)-1)//len(group)
   for n in group:
    if value:projected[n]=value
    else:projected.pop(n,None)
  return projected
