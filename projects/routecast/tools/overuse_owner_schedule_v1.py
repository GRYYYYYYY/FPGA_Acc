"""One-hop NET scheduling from the incoming round's owned resources and ledger."""
def select(dirty,owned,ledger,capacities):
 if not set(dirty)<=owned.keys():raise ValueError('unknown endpoint-dirty NET')
 overused={node for node,count in ledger.items() if count>capacities[node]}
 return sorted(set(dirty)|{net for net,nodes in owned.items() if nodes & overused})
