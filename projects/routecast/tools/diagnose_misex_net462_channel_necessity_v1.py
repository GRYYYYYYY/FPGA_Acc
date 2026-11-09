"""Budget alternatives to unique NET462 tree channels, exact seed and relaxed graph."""
import sys,json,time,heapq,struct
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net462_channel_necessity_v1_2026-10-07';out.mkdir();begin=time.perf_counter();parent=R/'experiments/misex_net466_expanded_tree_pool_v3_2026-10-07';vp=parent/'verification.json';pv=json.loads(vp.read_text());assert pv['proof']['finite_core_exhaustion_verified'];ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(vp):sha(vp),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()})
for name in ['seed.json','pool.json','protocol.json']:bindings[str(parent/name)]=sha(parent/name);assert pv['bindings'][str(parent/name)]==bindings[str(parent/name)]
pool=json.loads((parent/'pool.json').read_text());assert len(pool['462'])==1 and len(pool['462'][0]['records'])==1;rec=pool['462'][0]['records'][0];q={k:rec[k] for k in ['connection_id','net_id','source','sink']};seed=json.loads((parent/'seed.json').read_text());_,_,nodes,f,rc,queries=load_endpoints(ep);assert q==next(x for x in queries if x['connection_id']==q['connection_id']);slots={e:i for i,e in enumerate(f['edge_ids'])};channels=sorted(n for n in pool['462'][0]['nodes'] if nodes[n].get('type') in ('CHANX','CHANY'));assert channels;owners=defaultdict(set)
for x in seed:owners[x['net_id']].add(x['source']);owners[x['net_id']].update(f['dest_ranks'][slots[e]] for e in x['answer']['physical_edge_ids'])
assert not owners[462];base=Counter(n for s in owners.values() for n in s);floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};budget=max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2);cap=budget+1;ban_sets=[[]]+[[n] for n in channels]+([channels] if len(channels)>1 else []);(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,query=q,original_channel_nodes=channels,budget=budget,contexts=['exact_seed','all_seed_occupancy_relaxed'],ban_sets=ban_sets,scope='All single original channel bans plus all-channel ban/control. Original RC budget; exact kept/core/protected seed, then ALL seed capacity relaxed only as diagnostic. Relaxed witnesses never accepted routes; any fixed-seed legal alternative must still satisfy full27NET capacity.'),indent=2)+'\n');rows=[]
for context in ['exact_seed','all_seed_occupancy_relaxed']:
 for index,bans in enumerate(ban_sets):
  banned=set(bans);allowed=bytes((base[n]<f['capacities'][n] if context=='exact_seed' else f['capacities'][n]>0) and n not in banned for n in range(len(nodes)));d=[cap]*len(nodes);parents={};d[q['source']]=min(cap,rc.initial(q['source'])) if allowed[q['source']] else cap;queue=[(d[q['source']],q['source'])] if d[q['source']]<cap else []
  while queue:
   delay,u=heapq.heappop(queue)
   if d[u]!=delay:continue
   for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][edge]
    if not allowed[v]:continue
    cost=min(cap,delay+rc.increments[edge])
    if cost<d[v]:d[v]=cost;parents[v]=(u,edge);heapq.heappush(queue,(cost,v))
  folder=out/f'{context}_probe{index}';folder.mkdir();(folder/'allowed.bin').write_bytes(allowed);file=folder/'distances.bin';file.write_bytes(struct.pack('<'+str(len(nodes))+'Q',*d));path=None
  if d[q['sink']]<=budget:
   u=q['sink'];path=[];seen={u}
   while u!=q['source']:
    pnode,edge=parents[u];assert pnode not in seen;seen.add(pnode);path.append(f['edge_ids'][edge]);u=pnode
   path.reverse();assert rc.path(q['source'],q['sink'],path)==d[q['sink']]
  rows.append(dict(context=context,probe=index,banned_nodes=bans,minimum_capped_delay=d[q['sink']],budget_feasible=path is not None,physical_edge_ids=path,allowed_file=str(folder/'allowed.bin'),certificate_file=str(file)));print('CHANNEL PROBE',context,bans,d[q['sink']],budget,path is not None,flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,query=q,budget=budget,original_channel_nodes=channels,rows=rows,total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
