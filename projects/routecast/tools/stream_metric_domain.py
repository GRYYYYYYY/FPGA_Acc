"""Stream node-only metric domain, same integer occupancy spatial semantics."""
from collections import Counter,defaultdict
from fractions import Fraction
import xml.etree.ElementTree as ET

def metric_domain(graph_path,pv,tv):
 if any(type(v) is not int or v<0 for d in (pv,tv) for v in d.values()):raise ValueError('invalid integer occupancy')
 resources_p={};resources_t={};capacities=defaultdict(int);pd=defaultdict(int);td=defaultdict(int);all_caps={};wanted=set(pv)|set(tv);stack=[];counts=Counter()
 for event,node in ET.iterparse(graph_path,events=('start','end')):
  if event=='start':stack.append(node);continue
  parent_tag=stack[-2].tag if len(stack)>1 else None
  if node.tag=='node' and parent_tag=='rr_nodes':
   nid=node.attrib['id'];kind=node.attrib['type'];cap=int(node.attrib['capacity']);counts[kind]+=1
   if nid in wanted:all_caps[nid]=cap
   if kind in {'CHANX','CHANY'} and cap:
    resources_p[nid]=pv.get(nid,0)/cap;resources_t[nid]=tv.get(nid,0)/cap;loc=node.find('loc').attrib;segment=node.find('segment').attrib['segment_id']
    for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
     for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
      k=f'{x},{y},{kind},{segment}';capacities[k]+=cap;pd[k]+=pv.get(nid,0);td[k]+=tv.get(nid,0)
   stack[-2].remove(node);node.clear()
  if node.tag=='rr_nodes':break
  stack.pop()
 assert wanted<=set(all_caps);sp={k:float(Fraction(pd[k],c)) for k,c in capacities.items()};st={k:float(Fraction(td[k],c)) for k,c in capacities.items()};
 return resources_p,resources_t,sp,st,all_caps,dict(counts)
