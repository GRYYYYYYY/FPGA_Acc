"""Pure current-tree congestion eligibility; no timing-force/native equivalence."""
def decide(net,dirty,owned_nodes,ledger,capacities):
 if type(net) is not int or net<0:raise ValueError('NET domain')
 over=[]
 for node in owned_nodes:
  if type(node) is not int or not 0<=node<len(capacities):raise ValueError('owned node domain')
  cap=capacities[node];count=ledger.get(node,0)
  if type(cap) is not int or cap<1 or type(count) is not int or count<1:raise ValueError('owned occupancy/capacity domain')
  if count>cap:over.append(node)
 endpoint_dirty=net in dirty
 return dict(eligible=endpoint_dirty or bool(over),endpoint_dirty=endpoint_dirty,overused_nodes=sorted(set(over)))
