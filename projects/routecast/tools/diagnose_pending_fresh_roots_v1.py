"""Independent ordinary-path necessary conditions at saved fresh release roots."""
import sys,json,heapq,struct
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
parent=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3';out=R/'experiments/misex_fresh_root_diagnosis_v1_2026-10-07';out.mkdir();bp=parent/'misex3/batch14.json';fp=parent/'misex3/floors.json';ep=base/'endpoints.json';rp=parent/'receipt.json';row=next(r for r in json.loads(rp.read_text())['rows'] if r['name']=='misex3');bindings={**closure([Path(__file__)]),str(rp):sha(rp),str(ep):sha(ep)}
for file in (bp,fp):assert sha(file)==row['files'][str(file)];bindings[str(file)]=sha(file)
bindings.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()});assert all(sha(k)==h for k,h in bindings.items());(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Post-outcome saved batch14 initial and three proposed release roots. All four selected requests retained. Full original scalar-RC reverse minima under kept unique-NET capacities, excluding own NET occupancy, no saved-branch forbidden constraints and no tree restrictions. Necessary conditions for the same surrogate-budget joint root only; feasible ordinary paths do not prove joint tree feasibility, solver completeness, native quality or timing gain.'))+'\n')
graph,digest,nodes,f,rc,queries=load_endpoints(ep);event=json.loads(bp.read_text());floors={(v['source'],v['sink']):v['minimum_integer'] for v in json.loads(fp.read_text())};slots={e:s for s,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in event['before_records']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
n=len(nodes);reverse=[[] for _ in range(n)]
for u in range(n):
 for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][s]].append((u,s))
INF=(1<<64)-1;rows=[];releases=[event['initial_release_net_ids']]+event['owner_swap']['screening']['proposed']
for index,release in enumerate(releases):
 for query in event['selection']['queries']:
  occupancy=Counter(node for net,own in owners.items() if net not in release and net!=query['net_id'] for node in own);allowed=[f['capacities'][node]>occupancy[node] for node in range(n)];src,sink=query['source'],query['sink'];dist={};back={};queue=[]
  if allowed[sink]:dist[sink]=0;queue=[(0,sink)]
  while queue:
   d,v=heapq.heappop(queue)
   if dist[v]!=d:continue
   for u,s in reverse[v]:
    if not allowed[u]:continue
    nd=d+rc.increments[s]
    if nd<dist.get(u,INF):dist[u]=nd;back[u]=(v,s);heapq.heappush(queue,(nd,u))
  inequality_arcs=0
  for u in range(n):
   if not allowed[u]:continue
   for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][s]
    if allowed[v] and v in dist:assert u in dist and dist[u]<=rc.increments[s]+dist[v];inequality_arcs+=1
  minimum=None if not allowed[src] or src not in dist else rc.initial(src)+dist[src];path=[]
  if minimum is not None:
   u=src;seen=set()
   while u!=sink:assert u not in seen;seen.add(u);u,s=back[u];path.append(f['edge_ids'][s])
   assert rc.path(src,sink,path)==minimum
  floor=floors[(src,sink)];budget=max(rc.scale//10**9,(3*floor+1)//2);stem=f"release{index}_cid{query['connection_id']}";df=out/(stem+'_distance.bin');af=out/(stem+'_allowed.bin');df.write_bytes(b''.join(struct.pack('<Q',dist.get(i,INF)) for i in range(n)));af.write_bytes(bytes(allowed));rows.append(dict(release_index=index,release=release,query=query,budget=budget,minimum_integer=minimum,ordinary_budget_feasible=minimum is not None and minimum<=budget,physical_edge_ids=path,full_allowed_arc_inequalities=inequality_arcs,distance_file=str(df),distance_sha256=sha(df),allowed_file=str(af),allowed_sha256=sha(af)));print(release,query['connection_id'],minimum,budget,rows[-1]['ordinary_budget_feasible'],flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,bindings=bindings),indent=2)+'\n')
