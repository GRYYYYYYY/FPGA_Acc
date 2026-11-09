"""Bounded Pareto expansion inside original raw budget and frozen native tree.

No global capacity restriction: forecasts can overload. LABEL_LIMIT is UNKNOWN,
not infeasibility. NO_BUDGET_PATH refers only to this frozen partial tree.
"""
from types import SimpleNamespace
from tree_pareto_search_astar_v2 import search
LABEL_LIMIT=10000

def expand(tree,target,budget,fields,kinds,novelty,penalty,edge_slots,max_labels=LABEL_LIMIT):
 if type(budget) is not int or budget<0 or type(max_labels) is not int or max_labels<1:raise ValueError('budget/label bound')
 caps=[0 if (kinds[n]=='SOURCE' and n!=tree.source) or (kinds[n]=='SINK' and n!=target) else cap for n,cap in enumerate(fields['capacities'])];f=dict(fields,capacities=caps);initial={n:d for n,d in tree.arrival.items() if caps[n]>0 and (kinds[n]!='SINK' or n==target)};own=set(tree.arrival);spans=[int(n in novelty) for n in range(tree.n)]
 result=search(f,SimpleNamespace(increments=tree.inc),tree.source,target,initial,own,{},budget,spans,penalty,max_labels=max_labels);meta=dict(labels_created=result['labels_created'],expanded=result['expanded'],label_limit=max_labels)
 if result['status']!='FOUND':
  status={'LABEL_LIMIT':'UNKNOWN_LABEL_LIMIT','DEADLINE':'UNKNOWN_DEADLINE','NO_BUDGET_CAPACITY_PATH':'NO_BUDGET_PATH_FOR_FIXED_TREE'}[result['status']]
  return dict(status=status,committed=False,**meta)
 join=result['join'];tail=[edge_slots[e] for e in result['physical_edge_ids']];prefix=[];u=join
 while u!=tree.source:
  parent,slot=tree.parents[u];prefix.append(slot);u=parent
 prefix.reverse();path=tuple(prefix+tail);u=join;seen=set(own);value=tree.arrival[join];updates=[]
 for slot in tail:
  assert tree.offsets[u]<=slot<tree.offsets[u+1];v=tree.dest[slot];assert v not in seen and caps[v]>0;seen.add(v);value+=tree.inc[slot];updates.append((v,u,slot,value));u=v
 assert u==target and value==result['delay']<=budget
 assert result['cost']==value+penalty*sum(spans[tree.dest[s]] for s in tail)
 for v,parent,slot,arrival in updates:tree.parents[v]=(parent,slot);tree.arrival[v]=arrival
 return dict(status='COMMITTED',committed=True,raw=value,objective_numerator=result['cost'],objective_denominator=1,attach=join,new_nodes=len(tail),path_slots=path,**meta)
