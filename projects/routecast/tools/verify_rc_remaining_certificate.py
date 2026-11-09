"""Independent nonnegative RC shortest-remaining-distance certificate."""
from collections import deque
U64=(1<<64)-1

def verify(fields,increments,sink,remaining):
 n=len(fields['node_ids'])
 if type(sink) is not int or not 0<=sink<n or len(remaining)!=n or len(increments)!=len(fields['edge_ids']):raise ValueError('invalid certificate dimensions')
 if any(type(x) is not int or not 0<=x<=U64 for x in remaining) or remaining[sink]!=0:raise ValueError('invalid exact remaining distances')
 tight=[[] for _ in range(n)];edges=0
 for u in range(n):
  for i in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
   v=fields['dest_ranks'][i]
   if fields['costs'][i]==U64 or fields['capacities'][v]==0:continue
   delay=increments[i]
   if type(delay) is not int or delay<0:raise ValueError('nonnegative exact RC required')
   edges+=1
   if remaining[v]!=U64:
    if remaining[u]==U64 or remaining[u]>delay+remaining[v]:raise ValueError('failed distance inequality or false unreachable')
    if remaining[u]==delay+remaining[v]:tight[v].append(u)
 reached={sink};queue=deque([sink])
 while queue:
  v=queue.popleft()
  for u in tight[v]:
   if u not in reached:reached.add(u);queue.append(u)
 finite={u for u,d in enumerate(remaining) if d!=U64}
 if reached!=finite:raise ValueError('finite distance lacks tight path to sink')
 return {'finite_nodes':len(finite),'eligible_edges_checked':edges,'all_distance_and_tight_path_checks_passed':True}
