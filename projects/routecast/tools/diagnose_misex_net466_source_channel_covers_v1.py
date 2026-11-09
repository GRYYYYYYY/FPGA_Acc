"""Whole-NET source-channel cover necessary conditions with certified budgets."""
import sys,json,time,heapq,struct
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from tree_variant_capacity_packing_v1 import pack_variants
out=R/'experiments/misex_net466_source_channel_covers_v1_2026-10-07';out.mkdir();begin=time.perf_counter();parent=R/'experiments/misex_net466_expanded_tree_pool_v4_2026-10-07';vp=parent/'verification.json';pv=json.loads(vp.read_text());assert pv['proof']['finite_core_exhaustion_verified'];reservation=R/'experiments/misex_net462_channel_necessity_v1_2026-10-07';rvp=reservation/'verification.json';rv=json.loads(rvp.read_text());rrp=reservation/'receipt.json';assert sha(rrp)==rv['bindings'][str(rrp)];rr=json.loads(rrp.read_text());reserved=rr['original_channel_nodes'];assert all(not next(x for x in rr['rows'] if x['context']=='exact_seed' and x['banned_nodes']==[n])['budget_feasible'] for n in reserved);ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(vp):sha(vp),str(rvp):sha(rvp),str(rrp):sha(rrp),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()})
for name in ['seed.json','protocol.json']:bindings[str(parent/name)]=sha(parent/name);assert pv['bindings'][str(parent/name)]==bindings[str(parent/name)]
assert sha(parent/'seed.json')==rv['bindings'][str(R/'experiments/misex_net466_expanded_tree_pool_v3_2026-10-07/seed.json')];seed=json.loads((parent/'seed.json').read_text());pp=json.loads((parent/'protocol.json').read_text());core=[n for n in pv['proof']['core_nets'] if n!=462];_,_,nodes,f,rc,queries=load_endpoints(ep);channel=[n.get('type') in ('CHANX','CHANY') for n in nodes];slots={e:i for i,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in seed:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
base=Counter(n for s in owners.values() for n in s);assert all(f['capacities'][n]==1 and not base[n] for n in reserved);capacity_base=Counter(base);capacity_base.update(reserved);groups={n:pp['groups'][str(n)]+[{k:x[k] for k in ['connection_id','net_id','source','sink']} for x in seed if x['net_id']==n] for n in core};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,core_nets=core,reserved_for_net462=reserved,groups=groups,policy='ALL sink requests for six remaining finite-coreNETs plus sameNET immutable records. Non-CHAN shortest source prefix; start one forward distance field per firstCHAN. Query domains are budget-walk supersets, a necessary relaxation. Enumerate ALL source-channel subsets covering every non-direct query and retaining immutable first channels; remove supersets only after full enumeration. CrossNET new channel charge excludes sameNET seedownership; reserve mandatory462 channels. No actual omittedNET acceptance, parent/other channel occupancy relaxed only in domain diagnosis.'),indent=2)+'\n');rows=[];cover_options={}
for net in core:
 qs=sorted(groups[net],key=lambda q:q['connection_id']);assert len({q['source'] for q in qs})==1;src=qs[0]['source'];budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs};cap=max(budgets.values())+1;allowed=bytes(base[n]-int(n in owners[net])<f['capacities'][n] and n not in reserved for n in range(len(nodes)));prefix={src:rc.initial(src)} if allowed[src] and rc.initial(src)<cap else {};queue=[(prefix[src],src)] if prefix else [];first={}
 while queue:
  delay,u=heapq.heappop(queue)
  if prefix[u]!=delay:continue
  for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][edge];cost=delay+rc.increments[edge]
   if not allowed[v] or cost>=cap:continue
   if channel[v]:first[v]=min(cost,first.get(v,cap))
   elif cost<prefix.get(v,cap):prefix[v]=cost;heapq.heappush(queue,(cost,v))
 folder=out/f'net{net}';folder.mkdir();(folder/'allowed.bin').write_bytes(allowed);starts=sorted(first);assert len(starts)<=20,'Full cover enumeration limit; no partial proof';fields={};certs=[]
 for start in starts:
  d=[cap]*len(nodes);d[start]=first[start];queue=[(d[start],start)]
  while queue:
   delay,u=heapq.heappop(queue)
   if d[u]!=delay:continue
   for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][edge]
    if not allowed[v]:continue
    cost=min(cap,delay+rc.increments[edge])
    if cost<d[v]:d[v]=cost;heapq.heappush(queue,(cost,v))
  file=folder/f'first{start}.bin';file.write_bytes(struct.pack('<'+str(len(nodes))+'Q',*d));fields[start]=d;certs.append(dict(first_channel=start,source_prefix_delay=first[start],file=str(file)))
 domains=[dict(query=q,budget=budgets[q['connection_id']],no_channel_path=prefix.get(q['sink'],cap)<=budgets[q['connection_id']],first_channel_domain=[n for n in starts if fields[n][q['sink']]<=budgets[q['connection_id']]]) for q in qs];mandatory=set()
 for rec in seed:
  if rec['net_id']!=net:continue
  for eid in rec['answer']['physical_edge_ids']:
   v=f['dest_ranks'][slots[eid]]
   if channel[v]:mandatory.add(v);break
 assert mandatory<=set(starts);bits={n:1<<i for i,n in enumerate(starts)};required=sum(bits[n] for n in mandatory);domain_masks=[sum(bits[n] for n in row['first_channel_domain']) for row in domains if not row['no_channel_path']];allcovers=[mask for mask in range(1<<len(starts)) if mask&required==required and all(mask&d for d in domain_masks)];minimal=[mask for mask in allcovers if not any(mask!=m and m&mask==m for m in allcovers)];cover_options[net]=[[n for i,n in enumerate(starts) if mask>>i&1 and n not in owners[net]] for mask in minimal];rows.append(dict(net_id=net,cap=cap,starts=starts,prefix=prefix,first_prefix_delays=first,immutable_first_channels=sorted(mandatory),domains=domains,certificates=certs,all_cover_count=len(allcovers),minimal_cover_masks=minimal,cover_node_increments=cover_options[net]));print('SOURCE COVERS',net,len(qs),len(starts),len(minimal),[len(x) for x in cover_options[net]],flush=True)
result=pack_variants(f['capacities'],capacity_base,cover_options,max_nodes=100000,deadline=time.perf_counter()+120);assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,result=result,total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n');print('SOURCE COVER RESULT',result,flush=True)
