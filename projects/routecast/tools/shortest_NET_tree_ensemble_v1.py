"""Input-only equal-RC/min-hop rooted NET tree sampling reference.

Nonnegative integer edge costs; lexicographic (cost,hops) removes zero-cost
cycles from predecessor support. This restricts to minimum-hop RC minima,
not all RC-feasible routes. Samples share one parent per node across sinks.
"""
import heapq,hashlib,random

def prepare(edges,source,sinks):
 edges=tuple(edges);sinks=tuple(sorted(set(sinks)));assert type(source) is int and source>=0 and sinks
 adjacency={};ids=set()
 for eid,u,v,cost in edges:
  assert all(type(x) is int for x in (eid,u,v,cost)) and min(eid,u,v,cost)>=0 and eid not in ids
  ids.add(eid);adjacency.setdefault(u,[]).append((v,cost,eid))
 distance={source:(0,0)};parents={};queue=[(0,0,source)]
 while queue:
  cost,hops,u=heapq.heappop(queue)
  if distance[u]!=(cost,hops):continue
  for v,increment,eid in adjacency.get(u,[]):
   candidate=(cost+increment,hops+1);previous=distance.get(v)
   if previous is None or candidate<previous:
    distance[v]=candidate;parents[v]=[(u,eid)];heapq.heappush(queue,(*candidate,v))
   elif candidate==previous:parents[v].append((u,eid))
 if any(s not in distance for s in sinks):raise ValueError('unreachable NET sink')
 # Only parent choices that can lie on a sink's selected minimum path matter.
 support=set(sinks);pending=list(sinks)
 while pending:
  v=pending.pop()
  for u,_ in parents.get(v,[]):
   if u not in support:support.add(u);pending.append(u)
 assert source in support
 choices={v:tuple(sorted(parents[v])) for v in sorted(support-{source})}
 assert all(distance[u][1]+1==distance[v][1] for v,row in choices.items() for u,_ in row)
 return dict(source=source,sinks=sinks,choices=choices,distance={v:distance[v] for v in support})

def materialize(prepared,selected):
 source=prepared['source'];assert set(selected)==set(prepared['choices'])
 assert all(selected[v] in prepared['choices'][v] for v in selected)
 nodes={source};edge_ids=set();paths={}
 for sink in prepared['sinks']:
  v=sink;path=[];seen=set()
  while v!=source:
   assert v not in seen;seen.add(v);u,eid=selected[v];nodes.add(v);nodes.add(u);edge_ids.add(eid);path.append(eid);v=u
  paths[sink]=tuple(reversed(path))
 return dict(nodes=frozenset(nodes),edge_ids=frozenset(edge_ids),paths=paths,parents={v:selected[v] for v in nodes-{source}})

def sample(prepared,*,seed,net_id,sample_index):
 assert all(type(x) is int and x>=0 for x in (seed,net_id,sample_index))
 digest=hashlib.sha256(f'{seed}:{net_id}:{sample_index}'.encode()).digest();rng=random.Random(int.from_bytes(digest,'big'))
 selected={v:row[rng.randrange(len(row))] for v,row in prepared['choices'].items()}
 return materialize(prepared,selected)
