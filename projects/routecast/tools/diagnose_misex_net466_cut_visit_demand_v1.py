"""Layered additive-RC lower bounds on necessary distinct cut-node use."""
import sys,json,time,heapq,struct
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_cut_visit_demand_v1_2026-10-07';out.mkdir();domains=R/'experiments/misex_net466_first_channel_domains_v2_2026-10-07';dr=json.loads((domains/'receipt.json').read_text());dp=domains/'verification.json';verified=json.loads(dp.read_text());assert verified['queries_verified']==17;history=R/'experiments/misex_net466_extra_owner_joint_v17_2026-10-07/receipt.json';hr=json.loads(history.read_text());cut=sorted({int(n) for b in hr['attempts'][0]['branches'][-4:] for n in b['overuse_by_node']});bindings={**dr['bindings'],**closure([Path(__file__)]),str(domains/'receipt.json'):sha(domains/'receipt.json'),str(dp):sha(dp),str(history):sha(history)};assert all(sha(k)==h for k,h in bindings.items());(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cut_nodes=cut,queries='Frozen17 earliest/pending/critical queries from certified first-channel v2',scope='Necessary cut-node demand for simple SOURCE-SINK paths, fixed kept and original RC budgets; max per NET avoids double-counting shared trunks. No native or global-path feasibility inference.'),indent=2)+'\n');begin=time.perf_counter();_,_,nodes,f,rc,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');event=json.loads((R/'experiments/misex_net466_extra_owner_joint_v13_2026-10-07/event.json').read_text());release=set(dr['release']);slots={edge:i for i,edge in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in event['before_records']:
 if rec['net_id'] not in release:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[edge]] for edge in rec['answer']['physical_edge_ids'])
occupancy=Counter(n for own in owners.values() for n in own);allowed=bytes(f['capacities'][n]>occupancy[n] for n in range(len(nodes)));(out/'allowed.bin').write_bytes(allowed);cutset=set(cut);reverse=[[] for _ in nodes]
for u in range(len(nodes)):
 for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][edge]].append((u,edge))
INF=(1<<64)-1;rows=[]
for row in dr['rows']:
 q=row['query'];assert q['source'] not in cutset and q['sink'] not in cutset;previous={};costs=[];certificate=out/f"cid{q['connection_id']}_layers.bin"
 with certificate.open('wb') as stream:
  for layer in range(len(cut)+1):
   dist={q['sink']:0} if allowed[q['sink']] else {};queue=[(0,q['sink'])] if allowed[q['sink']] else []
   if layer:
    for v in cut:
     if not allowed[v] or v not in previous:continue
     for u,edge in reverse[v]:
      candidate=rc.increments[edge]+previous[v]
      if allowed[u] and candidate<dist.get(u,INF):dist[u]=candidate;heapq.heappush(queue,(candidate,u))
   while queue:
    delay,v=heapq.heappop(queue)
    if dist[v]!=delay:continue
    if v in cutset:continue
    for u,edge in reverse[v]:
     candidate=delay+rc.increments[edge]
     if allowed[u] and candidate<dist.get(u,INF):dist[u]=candidate;heapq.heappush(queue,(candidate,u))
   costs.append(None if q['source'] not in dist else rc.initial(q['source'])+dist[q['source']]);stream.write(b''.join(struct.pack('<Q',dist.get(n,INF)) for n in range(len(nodes))));previous=dist
 required=next((i for i,cost in enumerate(costs) if cost is not None and cost<=row['budget']),len(cut)+1);rows.append(dict(query=q,budget=row['budget'],minimum_required_cut_visits=required,minimum_delays_by_allowed_visits=costs,certificate_file=str(certificate),certificate_sha256=sha(certificate)));print(q['net_id'],q['connection_id'],required,flush=True)
demand=defaultdict(int)
for row in rows:demand[row['query']['net_id']]=max(demand[row['query']['net_id']],row['minimum_required_cut_visits'])
capacity=sum(f['capacities'][n]-occupancy[n] for n in cut);assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,release=sorted(release),cut_nodes=cut,rows=rows,minimum_node_units_by_net=dict(demand),minimum_total_node_units=sum(demand.values()),residual_node_units=capacity,necessary_capacity_violation=sum(demand.values())>capacity,total_component_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');print('Cut demand',dict(demand),sum(demand.values()),capacity,flush=True)
