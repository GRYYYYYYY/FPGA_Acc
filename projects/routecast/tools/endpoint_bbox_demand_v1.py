"""Unfitted endpoint-only uniform bbox, perNET directional demand / capacity."""
from collections import defaultdict
from fractions import Fraction

def predict(nodes,queries):
 groups=defaultdict(set);capacities=defaultdict(int);directional=defaultdict(int)
 for q in queries:groups[q['net_id']].update((q['source'],q['sink']))
 for n,node in nodes.items():
  if node.type not in ('CHANX','CHANY') or node.capacity<=0:continue
  loc=dict(node.location);layer=int(loc.get('layer','0'))
  for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
   for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
    k=(layer,x,y,node.type,node.segment_id if node.segment_id is not None else -1);capacities[k]+=node.capacity;directional[k[:4]]+=node.capacity
 demand=defaultdict(Fraction)
 for owned in groups.values():
  locations=[dict(nodes[n].location) for n in owned];layers={int(l.get('layer','0')) for l in locations};assert len(layers)==1,'Cross-layer geometry requires an explicit baseline';layer=next(iter(layers));lo=min(int(l['xlow']) for l in locations);hi=max(int(l['xlow']) for l in locations);bottom=min(int(l['ylow']) for l in locations);top=max(int(l['ylow']) for l in locations);dx=hi-lo;dy=top-bottom;area=(dx+1)*(dy+1)
  for x in range(lo,hi+1):
   for y in range(bottom,top+1):demand[layer,x,y,'CHANX']+=Fraction(dx,area);demand[layer,x,y,'CHANY']+=Fraction(dy,area)
 return {k:float(demand[k[:4]]/directional[k[:4]]) for k in capacities},dict(capacities)
