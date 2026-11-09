"""Causal two-frame expected other-owner demand, in exact half-count units."""
def predict(current_owners,current_counts,previous_owners,previous_counts):
 # Query domain fixed from current inputs, independent of future route labels.
 if previous_owners is None:previous_owners,previous_counts=current_owners,current_counts
 result={}
 for net,nodes in current_owners.items():
  previous=previous_owners[net]
  for node in nodes:
   value=current_counts[node]-1+previous_counts[node]-int(node in previous)
   assert value>=0
   result[net,node]=value
 return result
