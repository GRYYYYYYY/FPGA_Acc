"""Exact finite complete-NET-tree selection with lexicographic resource objective.

Per-sink RC budgets are enforced by tree admission before calling select.
Primary: sum of per-NET unique node resource spans. Secondary: total per-sink
additive RC excess. Sharing within a NET is charged once; different NETs
remain distinct consumers even if resource capacity permits sharing.
"""
def select(banks,capacities,spans,fixed_occupancy=None,max_states=100000):
 """Each candidate is an admitted complete tree; occupancy once per NET/node.

fixed_occupancy excludes every NET represented in banks. Exhaustion proves
only the finite bank result. A limited run never claims infeasibility/optimality.
 """
 def add(a,b):return (a[0]+b[0],a[1]+b[1])
 def objective(c):return (sum(spans.get(v,0) for v in c['nodes']),c['excess'])
 fixed={} if fixed_occupancy is None else dict(fixed_occupancy)
 if type(max_states) is not int or max_states<1:raise ValueError('state limit')
 for node,value in fixed.items():
  if type(value) is not int or value<0 or type(capacities.get(node)) is not int or value>capacities[node]:raise ValueError('invalid fixed occupancy')
 for net,bank in banks.items():
  if type(net) is not int or net<0:raise ValueError('NET identity')
  for c in bank:
   if type(c.get('excess')) is not int or c['excess']<0 or not isinstance(c.get('nodes'),frozenset):raise ValueError('unadmitted candidate')
   for node in c['nodes']:
    if type(spans.get(node,0)) is not int or spans.get(node,0)<0:raise ValueError('invalid node resource span')
    if type(capacities.get(node)) is not int or capacities[node]<=0:raise ValueError('candidate capacity')
 if any(not bank for bank in banks.values()):return dict(status='INFEASIBLE_WITHIN_CANDIDATES',selection=None,objective=None,states=0)
 order=sorted(banks,key=lambda n:(len(banks[n]),n));minimum=[min(objective(c) for c in banks[n]) for n in order];suffix=[(0,0)]*(len(order)+1)
 for i in range(len(order)-1,-1,-1):suffix[i]=add(suffix[i+1],minimum[i])
 stack=[(0,{},fixed,(0,0))];states=0;best=None;bestcost=None
 while stack:
  if states>=max_states:return dict(status='UNKNOWN_STATE_LIMIT',selection=best,objective=bestcost,states=states)
  depth,chosen,occ,total=stack.pop();states+=1
  if bestcost is not None and add(total,suffix[depth])>=bestcost:continue
  if depth==len(order):best=chosen;bestcost=total;continue
  net=order[depth]
  for ci in reversed(range(len(banks[net]))):
   c=banks[net][ci]
   if any(occ.get(v,0)+1>capacities[v] for v in c['nodes']):continue
   updated=dict(occ)
   for v in c['nodes']:updated[v]=updated.get(v,0)+1
   stack.append((depth+1,chosen|{net:ci},updated,add(total,objective(c))))
 return dict(status='OPTIMAL_WITHIN_CANDIDATES' if best is not None else 'INFEASIBLE_WITHIN_CANDIDATES',selection=best,objective=bestcost,states=states)
