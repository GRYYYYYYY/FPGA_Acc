"""Atomic wholeNET delta updates for fixed-graph endpoint messages, no labels."""
from collections import defaultdict,Counter
from endpoint_graph_signals_v1 import extract
MAX=2**64-1
class State:
 def __init__(self,node_ids,edges,queries,NETs):
  queries=list(queries);self.nodes=tuple(node_ids);self.edges=tuple(edges);self.values=extract(self.nodes,self.edges,queries,NETs);self.outgoing=defaultdict(list);self.incoming=defaultdict(list)
  for a,b in self.edges:self.outgoing[a].append(b);self.incoming[b].append(a)
  self.NETs={};self.cid_owner={};self.epoch=0;by_net=defaultdict(list)
  for q in queries:by_net[q['net_id']].append(q)
  for net,qs in by_net.items():
   frozen=self.freeze(net,qs,NETs[net]);self.NETs[net]=frozen
   for cid,source,sink in frozen['queries']:self.cid_owner[cid]=net
 def freeze(self,net,queries,feature):
  if type(net) is not int:raise ValueError('integer NET ID required')
  queries=list(queries);qs=tuple(sorted((q['connection_id'],q['source'],q['sink']) for q in queries))
  if not qs or len({q[0] for q in qs})!=len(qs) or any(type(c) is not int or c<0 or type(s) is not int or type(t) is not int or s not in self.values or t not in self.values for c,s,t in qs) or any(type(q['net_id']) is not int or q['net_id']!=net for q in queries):raise ValueError('wholeNET query identity')
  bbox=tuple(feature['endpoint_bbox']);source=feature['source_RR']
  if feature['fanout']!=len(qs) or {q[1] for q in qs}!={source} or len(bbox)!=4 or any(type(x) is not int for x in bbox) or bbox[2]<bbox[0] or bbox[3]<bbox[1]:raise ValueError('wholeNET feature dimensions')
  return {'queries':qs,'source_RR':source,'bbox':bbox}
 @staticmethod
 def contribution(record):
  result=defaultdict(lambda:[0]*5);source=record['source_RR'];bbox=record['bbox'];span=bbox[2]-bbox[0]+bbox[3]-bbox[1]+2;result[source][:3]=[1,len(record['queries']),span]
  for cid,s,t in record['queries']:result[t][3]+=1;result[t][4]+=span
  return dict(result)
 def update(self,upserts,removes,expected_epoch,new_epoch):
  if any(type(v) is not int or not 0<=v<=MAX for v in [expected_epoch,new_epoch]) or expected_epoch!=self.epoch or new_epoch!=expected_epoch+1:raise ValueError('stale/invalid epoch')
  removes=list(removes)
  if len(removes)!=len(set(removes)) or set(removes)&set(upserts) or not set(removes)<=set(self.NETs):raise ValueError('invalid NET removal')
  prepared={n:self.freeze(n,record['queries'],record['feature']) for n,record in upserts.items()};changed={n for n,r in prepared.items() if self.NETs.get(n)!=r}|set(removes)
  if not changed:return {'status':'UNCHANGED','epoch':self.epoch,'changed_NETs':[],'changed_RRs':[],'edge_visits':0}
  new_cids={}
  for n,r in prepared.items():
   for cid,s,t in r['queries']:
    if cid in new_cids or cid in self.cid_owner and self.cid_owner[cid] not in changed and self.cid_owner[cid]!=n:raise ValueError('CID ownership collision')
    new_cids[cid]=n
  delta=defaultdict(lambda:[0]*15)
  for net in changed:
   for record,sign in [(self.NETs.get(net),-1),(prepared.get(net),1)]:
    if record is None:continue
    for node,base in self.contribution(record).items():
     for i,v in enumerate(base):delta[node][i]+=sign*v
  visits=0
  for forward,start,end,offset in [(True,0,3,5),(False,3,5,11)]:
   adjacency=self.outgoing if forward else self.incoming;current={n:v[start:end] for n,v in list(delta.items()) if any(v[start:end])}
   for hop in range(2):
    nxt=defaultdict(lambda:[0]*(end-start))
    for n,vector in current.items():
     for neighbor in adjacency.get(n,[]):
      visits+=1
      for i,value in enumerate(vector):nxt[neighbor][i]+=value
    current={n:v for n,v in nxt.items() if any(v)}
    for n,v in current.items():
     for i,value in enumerate(v):delta[n][offset+hop*(end-start)+i]+=value
  updates={n:[a+b for a,b in zip(self.values[n],v)] for n,v in delta.items() if any(v)}
  if any(v<0 for values in updates.values() for v in values):raise ValueError('negative resulting signal')
  # Every check above precedes mutation of state, epochs, CIDs or NET definitions.
  for net in changed:
   previous=self.NETs.pop(net,None)
   if previous:
    for cid,s,t in previous['queries']:del self.cid_owner[cid]
  self.NETs.update(prepared);self.cid_owner.update(new_cids);self.values.update(updates);self.epoch=new_epoch
  return {'status':'COMMITTED','epoch':new_epoch,'changed_NETs':sorted(changed),'changed_RRs':sorted(updates),'edge_visits':visits}
