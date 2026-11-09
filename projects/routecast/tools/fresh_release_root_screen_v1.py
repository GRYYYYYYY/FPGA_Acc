"""Ordinary scalar-RC budget necessary conditions for fixed-kept fresh joint roots."""
from collections import defaultdict
from types import MappingProxyType
from remaining_delay_session_cache_v5 import FrozenRC
from pending_owner_joint_repair_v3 import constrained_witness
class FreshRootScreen:
 def __init__(self,fields,rc,before,floors):
  self.fields=MappingProxyType({k:tuple(v) for k,v in fields.items()});self.rc=FrozenRC(self.fields,rc);self.floors=dict(floors);slots={e:s for s,e in enumerate(self.fields['edge_ids'])};owners=defaultdict(set);seen=set()
  for record in before:
   cid=record['connection_id']
   if cid in seen:raise ValueError('duplicate before identity')
   seen.add(cid);assert self.rc.path(record['source'],record['sink'],record['answer']['physical_edge_ids'])==record['answer']['delay']<=record['budget_integer'];net=record['net_id'];owners[net].add(record['source']);owners[net].update(self.fields['dest_ranks'][slots[e]] for e in record['answer']['physical_edge_ids'])
  by_node=defaultdict(set)
  for net,nodes in owners.items():
   for node in nodes:by_node[node].add(net)
  assert all(len(nets)<=self.fields['capacities'][node] for node,nets in by_node.items())
  self.owners={net:frozenset(nodes) for net,nodes in owners.items()};self.saturated=frozenset(node for node,nets in by_node.items() if len(nets)==self.fields['capacities'][node]);self.memo={};self.before_ids=frozenset(seen)
 def check(self,release,queries,deadline=None):
  release=frozenset(release)
  if not release or not release<=self.owners.keys():raise ValueError('unknown release NET')
  ids=[q['connection_id'] for q in queries]
  if not ids or len(set(ids))!=len(ids) or self.before_ids.intersection(ids):raise ValueError('invalid selected scope')
  freed=set().union(*(self.owners[net] for net in release));rows=[]
  for query in queries:
   forbidden=self.saturated-freed-self.owners.get(query['net_id'],frozenset());key=(release,query['net_id'],query['source'],query['sink']);witness=self.memo.get(key)
   if key not in self.memo:witness=constrained_witness(self.fields,self.rc,query,forbidden,deadline);self.memo[key]=witness
   floor=self.floors[(query['source'],query['sink'])];budget=max(self.rc.scale//10**9,(3*floor+1)//2);rows.append(dict(query=dict(query),budget=budget,witness=witness,ordinary_budget_feasible=witness is not None and witness['minimum_integer']<=budget))
  return dict(release=sorted(release),queries=rows,all_selected_ordinary_budget_feasible=all(row['ordinary_budget_feasible'] for row in rows),scope='Necessary fixed-kept ordinary scalar-RC conditions only, not joint feasibility or solver completeness; no saved branch forbidden constraints.')
