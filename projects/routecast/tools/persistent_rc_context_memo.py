"""Single-owner buffered-RC graph context with validated replaceable history.

Callers own route ledgers and serialization. This interface owns native demand
and cost buffers; it is synchronous and does not provide concurrent publication.
"""
import json
from pathlib import Path
from pre_route_endpoints import sha
from collections import defaultdict
from nonzero_rc_endpoint_context_memo import load_endpoints
from native_capacity_rc_search import NativeCapacityRC

class PersistentRCContext:
 def __init__(self,endpoint_path):
  self.context=load_endpoints(endpoint_path)
  self.rc=self.context[4]
  self.native=NativeCapacityRC(self.rc)
  self.destination_slots=defaultdict(list)
  for slot,node in enumerate(self.rc.fields['dest_ranks']):
   self.destination_slots[node].append(slot)
   self.native.arrays[3][slot]=self.rc.increments[slot]
  self.history={}
  self.endpoint_metadata=json.loads(Path(endpoint_path).read_text())
 def set_history(self,history):
  """Replace history; validate and stage all costs before publishing any change."""
  staged={}
  for node,count in history.items():
   if type(node) is not int or not 0<=node<self.native.n or type(count) is not int or count<0:
    raise ValueError('history requires valid node and nonnegative integer count')
   if count:staged[node]=count
  updates=[]
  for node in self.history.keys()|staged.keys():
   if self.history.get(node,0)==staged.get(node,0):continue
   for slot in self.destination_slots.get(node,()):
    cost=self.rc.increments[slot]*(1+staged.get(node,0))
    if not 0<=cost<(1<<64):raise ValueError('history cost exceeds uint64 transport')
    updates.append((slot,cost))
  for slot,cost in updates:self.native.arrays[3][slot]=cost
  self.history=staged
 def reset(self):
  """Reset mutable history/demand; preserve authenticated graph and arrays."""
  self.set_history({})
  self.native.set_other({})
 def query(self,source,sink,budget,other,max_labels=10000):
  self.native.set_other(other)
  return self.native.query(source,sink,budget,max_labels=max_labels)

 def bind_endpoints(self,endpoint_path):
  """Bind same-netlist/same-RR placement endpoints without reparsing the graph.

  Return wholeNET affected cohort. Callers must repair/remove stale route records
  before publication; this operation does not update a route ledger.
  """
  staged=json.loads(Path(endpoint_path).read_text())
  inputs=staged['inputs']
  for value in inputs.values():
   if sha(value['path'])!=value['sha256']:raise ValueError('changed endpoint input')
  if staged['graph_sha256']!=self.context[1] or inputs['graph']['sha256']!=self.context[1]:raise ValueError('RR graph identity changed')
  if sha(self.context[0])!=self.context[1]:raise ValueError('original RR graph changed')
  if inputs['net']['sha256']!=self.endpoint_metadata['inputs']['net']['sha256'] or staged['net_names']!=self.endpoint_metadata['net_names']:raise ValueError('netlist identity changed')
  old={q['connection_id']:q for q in self.context[5]};new={}
  for q in staged['connections']:
   cid=q['connection_id'];net=q['net_id']
   if type(cid) is not int or not 0<=cid<(1<<64) or cid in new:raise ValueError('invalid connection identity')
   if cid not in old or type(net) is not int or net!=old[cid]['net_id']:raise ValueError('connection NET identity changed')
   for key,kind in [('source','SOURCE'),('sink','SINK')]:
    node=q[key]
    if type(node) is not int or not 0<=node<self.native.n or self.context[2][node].get('type')!=kind:raise ValueError('invalid physical endpoint')
   new[cid]=q
  if set(new)!=set(old):raise ValueError('connection cohort changed')
  sources={}
  for q in new.values():
   if q['net_id'] in sources and sources[q['net_id']]!=q['source']:raise ValueError('multiple NET sources')
   sources[q['net_id']]=q['source']
  changed=sorted(cid for cid in old if old[cid]!=new[cid]);nets=sorted({new[cid]['net_id'] for cid in changed})
  cohort=sorted(cid for cid,q in new.items() if q['net_id'] in nets)
  result={'changed_connection_ids':changed,'affected_net_ids':nets,'affected_complete_net_connection_ids':cohort}
  # Commit only endpoint metadata/list; no native history/demand/cost mutation.
  self.context=(*self.context[:5],staged['connections'])
  self.endpoint_metadata=staged
  return result
