"""Generate complete trees restricted by independently verified source covers."""
import sys,json,time,heapq
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from tree_variant_capacity_packing_v1 import pack_variants
out=R/'experiments/misex_net466_expanded_tree_pool_v5_2026-10-07';out.mkdir();begin=time.perf_counter();parent=R/'experiments/misex_net466_expanded_tree_pool_v4_2026-10-07';covers=R/'experiments/misex_net466_source_channel_covers_v1_2026-10-07';vp=parent/'verification.json';pv=json.loads(vp.read_text());cvp=covers/'verification.json';cv=json.loads(cvp.read_text());assert cv['all_cover_subsets_and_minimal_antichains_verified'];crp=covers/'receipt.json';assert sha(crp)==cv['bindings'][str(crp)];cr=json.loads(crp.read_text());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(vp):sha(vp),str(cvp):sha(cvp),str(crp):sha(crp),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()})
for name in ['seed.json','event.json','protocol.json','pool.json']:bindings[str(parent/name)]=sha(parent/name);assert pv['bindings'][str(parent/name)]==bindings[str(parent/name)]
p=json.loads((parent/'protocol.json').read_text());seed=json.loads((parent/'seed.json').read_text());groups={int(n):qs for n,qs in p['groups'].items()};pools={int(n):ops for n,ops in json.loads((parent/'pool.json').read_text()).items()};_,_,nodes,f,rc,queries=load_endpoints(ep);slots={e:i for i,e in enumerate(f['edge_ids'])};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};seedowners=defaultdict(set)
def own(records):return {x['source'] for x in records}|{f['dest_ranks'][slots[e]] for x in records for e in x['answer']['physical_edge_ids']}
for rec in seed:seedowners[rec['net_id']].update(own([rec]))
base=Counter(n for s in seedowners.values() for n in s);generated=[];reserved=json.loads((covers/'protocol.json').read_text())['reserved_for_net462']
for coverrow in cr['rows']:
 net=coverrow['net_id'];src=groups[net][0]['source'];cap=coverrow['cap']
 for cover_index,mask in enumerate(coverrow['minimal_cover_masks']):
  selected=[n for i,n in enumerate(coverrow['starts']) if mask>>i&1];banned=set(reserved)|set(coverrow['starts'])-set(selected);assert not banned.intersection(seedowners[net]);allowed=bytes(base[n]-int(n in seedowners[net])<f['capacities'][n] and n not in banned for n in range(len(nodes)));d=[cap]*len(nodes);parents={};queue=[];records=[];construction='source_cover_restricted_shortest_tree'
  if seedowners[net]:
   construction='source_cover_restricted_immutable_prefix_extension'
   for rec in seed:
    if rec['net_id']!=net:continue
    u=rec['source'];delay=rc.initial(u);d[u]=min(cap,delay)
    for eid in rec['answer']['physical_edge_ids']:
     edge=slots[eid];v=f['dest_ranks'][edge];assert v not in parents or parents[v]==(u,edge);parents[v]=(u,edge);delay+=rc.increments[edge];d[v]=min(cap,delay);u=v
   for n in seedowners[net]:
    if d[n]<cap:heapq.heappush(queue,(d[n],n))
  elif allowed[src]:d[src]=min(cap,rc.initial(src));heapq.heappush(queue,(d[src],src))
  while queue:
   delay,u=heapq.heappop(queue)
   if delay!=d[u]:continue
   for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][edge]
    if v in seedowners[net] or not allowed[v]:continue
    cost=min(cap,delay+rc.increments[edge])
    if cost<d[v]:d[v]=cost;parents[v]=(u,edge);heapq.heappush(queue,(cost,v))
  reached={n for n,x in enumerate(d) if x<cap}
  if not all(q['sink'] in reached and d[q['sink']]<=max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in groups[net]):
   generated.append(dict(net_id=net,cover_index=cover_index,selected_source_channels=selected,added_variant=False,connections=0,construction=construction,status='NO_COMPLETE_EXTENSION'));continue
  for q in sorted(groups[net],key=lambda q:q['connection_id']):
   u=q['sink'];assert u in reached;path=[]
   while u!=src:pnode,edge=parents[u];path.append(f['edge_ids'][edge]);u=pnode
   path.reverse();floor=floors[src,q['sink']];budget=max(rc.scale//10**9,(3*floor+1)//2);assert rc.path(src,q['sink'],path)==d[q['sink']]<=budget;records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=d[q['sink']]),budget_integer=budget,floor_integer=floor))
  statefile=out/f'generated_net{net}_cover{cover_index}.json';statefile.write_text(json.dumps(dict(records=records,failure=None,construction=construction,seed_file=str(out/'seed.json'),cover_index=cover_index,selected_source_channels=selected,banned_nodes=sorted(banned)))+'\n');sig=tuple((x['connection_id'],tuple(x['answer']['physical_edge_ids'])) for x in records);old={tuple((x['connection_id'],tuple(x['answer']['physical_edge_ids'])) for x in op['records']) for op in pools[net]};added=sig not in old
  if added:pools[net].append(dict(records=records,nodes=sorted(own(records)-seedowners[net]),origin=str(statefile)))
  generated.append(dict(net_id=net,cover_index=cover_index,selected_source_channels=selected,added_variant=added,connections=len(records),construction=construction));print('CERTIFIED TREE',net,cover_index,len(records),added,flush=True)
(out/'seed.json').write_text(json.dumps(seed)+'\n');(out/'event.json').write_text((parent/'event.json').read_text());(out/'pool.json').write_text(json.dumps(pools)+'\n');(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,groups=groups,search_seconds=120,max_nodes=100000,generated=generated,policy='Previous261 complete variants plus complete source-cover-constrained candidates for six core NETs; stronger candidate-generation bans apply to all appearances of unselected first channels. Complete immutable-prefix preservation and original budgets; no shortest completeness claim; node choices subtract only same NET seed-owned nodes so protected trunk charged once, other NET seed occupancy remains. All27groups/full2172CID required, compact paths with immutable seed. Finite pooling only, no all-path/native proof.'),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());start=time.perf_counter();result=pack_variants(f['capacities'],base,{n:[op['nodes'] for op in ops] for n,ops in pools.items()},max_nodes=100000,deadline=start+120);solution=None
if result['status']=='FOUND_POOL_BATCH':
 records=seed+[rec for n,i in result['chosen_option_indices'].items() for rec in pools[n][i]['records']];assert len({x['connection_id'] for x in records})==len(records)==2172;owners=defaultdict(set)
 for rec in records:owners[rec['net_id']].update(own([rec]))
 ledger=Counter(n for s in owners.values() for n in s);assert all(c<=f['capacities'][n] for n,c in ledger.items());solution=dict(records=sorted(records,key=lambda x:x['connection_id']),ledger=dict(ledger),failure=None,completed_connections=len(records),required_connections=len(queries),pending_connection_ids=sorted({q['connection_id'] for q in queries}-{x['connection_id'] for x in records}),selected_origins={str(n):pools[n][i]['origin'] for n,i in result['chosen_option_indices'].items()})
checks=[];core=sorted(pools)
if result['status']=='POOL_EXHAUSTED':
 for n in sorted(pools):
  remaining=[x for x in core if x!=n];probe=pack_variants(f['capacities'],base,{x:[op['nodes'] for op in pools[x]] for x in remaining},max_nodes=100000,deadline=start+120);checks.append(dict(removed_net=n,nets=remaining,result=probe))
  if probe['status']=='POOL_EXHAUSTED':core=remaining
(out/'candidate.json').write_text(json.dumps(solution)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,result=result,generated=generated,variant_counts={n:len(ops) for n,ops in pools.items()},core_nets=core,diagnostic_deletion_checks=checks,completed=None if solution is None else len(solution['records']),required=len(queries),total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');print('POOL',result, 'CORE',core, 'COUNTS', {n:len(ops) for n,ops in pools.items()},flush=True)
