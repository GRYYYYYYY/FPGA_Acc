"""Exact capacity-coupled selection of finite complete rooted NET-tree banks.

Objective: sum of per-sink additive RC excess above caller-supplied floors.
Not STA, full-graph optimality, or a candidate generation policy.
"""
def tree_candidate(edges,source,sink_paths,floors,budgets,capacities,kinds):
 if set(sink_paths)!=set(floors) or set(floors)!=set(budgets) or not sink_paths:
  raise ValueError('sink/floor/budget domain')
 if kinds.get(source)!='SOURCE':raise ValueError('source kind')
 arcs={}
 for eid,u,v,w in edges:
  if any(type(x) is not int or x<0 for x in [eid,u,v,w]) or eid in arcs:raise ValueError('edge identity/cost')
  arcs[eid]=(u,v,w)
 nodes={source};parents={};used=set();costs={};paths={}
 for sink,path in sorted(sink_paths.items()):
  if kinds.get(sink)!='SINK' or any(type(x) is not int or x<0 for x in [floors[sink],budgets[sink]]):raise ValueError('sink or RC bound')
  u=source;seen={source};value=0;path=tuple(path)
  for eid in path:
   if eid not in arcs:raise ValueError('unknown physical edge')
   a,b,w=arcs[eid]
   if a!=u or b in seen or kinds.get(a)=='SINK' or kinds.get(b)=='SOURCE':raise ValueError('invalid rooted path')
   if b in parents and parents[b]!=(a,eid):raise ValueError('NET has multiple parents')
   parents[b]=(a,eid);nodes.add(b);seen.add(b);used.add(eid);value+=w;u=b
  if u!=sink or not floors[sink]<=value<=budgets[sink]:raise ValueError('sink endpoint or RC budget')
  costs[sink]=value;paths[sink]=path
 for node in nodes:
  if type(capacities.get(node)) is not int or capacities[node]<=0:raise ValueError('nonpositive or missing node capacity')
 return dict(nodes=frozenset(nodes),edge_ids=frozenset(used),parents=parents,paths=paths,sink_costs=costs,excess=sum(costs[s]-floors[s] for s in costs))

def select(banks,capacities,fixed_occupancy=None,max_states=100000):
 """Each candidate is an admitted complete tree; occupancy once per NET/node.

fixed_occupancy excludes every NET represented in banks. Exhaustion proves
only the finite bank result. A limited run never claims infeasibility/optimality.
 """
 fixed={} if fixed_occupancy is None else dict(fixed_occupancy)
 if type(max_states) is not int or max_states<1:raise ValueError('state limit')
 for node,value in fixed.items():
  if type(value) is not int or value<0 or type(capacities.get(node)) is not int or value>capacities[node]:raise ValueError('invalid fixed occupancy')
 for net,bank in banks.items():
  if type(net) is not int or net<0:raise ValueError('NET identity')
  for c in bank:
   if type(c.get('excess')) is not int or c['excess']<0 or not isinstance(c.get('nodes'),frozenset):raise ValueError('unadmitted candidate')
   for node in c['nodes']:
    if type(capacities.get(node)) is not int or capacities[node]<=0:raise ValueError('candidate capacity')
 if any(not bank for bank in banks.values()):return dict(status='INFEASIBLE_WITHIN_CANDIDATES',selection=None,excess=None,states=0)
 order=sorted(banks,key=lambda n:(len(banks[n]),n));minimum=[min(c['excess'] for c in banks[n]) for n in order];suffix=[0]*(len(order)+1)
 for i in range(len(order)-1,-1,-1):suffix[i]=suffix[i+1]+minimum[i]
 stack=[(0,{},fixed,0)];states=0;best=None;bestcost=None
 while stack:
  if states>=max_states:return dict(status='UNKNOWN_STATE_LIMIT',selection=best,excess=bestcost,states=states)
  depth,chosen,occ,total=stack.pop();states+=1
  if bestcost is not None and total+suffix[depth]>=bestcost:continue
  if depth==len(order):best=chosen;bestcost=total;continue
  net=order[depth]
  for ci in reversed(range(len(banks[net]))):
   c=banks[net][ci]
   if any(occ.get(v,0)+1>capacities[v] for v in c['nodes']):continue
   updated=dict(occ)
   for v in c['nodes']:updated[v]=updated.get(v,0)+1
   stack.append((depth+1,chosen|{net:ci},updated,total+c['excess']))
 return dict(status='OPTIMAL_WITHIN_CANDIDATES' if best is not None else 'INFEASIBLE_WITHIN_CANDIDATES',selection=best,excess=bestcost,states=states)
