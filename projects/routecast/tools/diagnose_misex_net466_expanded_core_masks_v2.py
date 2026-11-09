"""Full-query necessary resource domains of the expanded five-NET finite core."""
import sys,json,time,heapq,struct
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from tree_variant_capacity_packing_v1 import pack_variants
out=R/'experiments/misex_net466_expanded_core_masks_v2_2026-10-07';out.mkdir();begin=time.perf_counter();parent=R/'experiments/misex_net466_expanded_tree_pool_v2_2026-10-07';vp=parent/'verification.json';pv=json.loads(vp.read_text());assert pv['proof']['finite_core_exhaustion_verified'];ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(vp):sha(vp),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()})
for name in ['seed.json','protocol.json','pool.json']:bindings[str(parent/name)]=sha(parent/name);assert pv['bindings'][str(parent/name)]==bindings[str(parent/name)]
core=pv['proof']['core_nets'];pool={int(n):ops for n,ops in json.loads((parent/'pool.json').read_text()).items()};pp=json.loads((parent/'protocol.json').read_text());seed=json.loads((parent/'seed.json').read_text());_,_,nodes,f,rc,queries=load_endpoints(ep);slots={e:i for i,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in seed:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
base=Counter(n for s in owners.values() for n in s);groups={n:pp['groups'][str(n)]+[{k:x[k] for k in ['connection_id','net_id','source','sink']} for x in seed if x['net_id']==n] for n in core};protected={q[k] for qs in groups.values() for q in qs for k in ['source','sink']};occ={n:Counter(node for op in pool[n] for node in op['nodes']) for n in core};scores={node:sum(occ[a][node]*occ[b][node] for i,a in enumerate(core) for b in core[i+1:]) for node in set().union(*(set(c) for c in occ.values()))};cut=sorted(sorted((n for n,s in scores.items() if s>0 and not base[n] and n not in protected and nodes[n].get('type') in ('CHANX','CHANY')),key=lambda n:(-scores[n],n))[:5]);assert len(cut)==5;(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,core_nets=core,cut_nodes=cut,rank_policy='Top5 sum pairwise variant occurrence products, unowned by immutable seed, nonendpoint channel nodes; tie rawnode ascending.',groups=groups,policy='All32masks per coreNET; ALL original group plus immutable sameNET connections. Original budgets, exact immutable seed occupancy minus sameNET charge. Other mutable NETs and parent constraints relaxed only for necessary-condition diagnosis. Reduce feasible mask supersets only after enumerating all32; finite exact cut-capacity packing.'),indent=2)+'\n');floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};rows=[];domains={};minimal={}
for net in core:
 qs=sorted(groups[net],key=lambda q:q['connection_id']);assert len(qs)==len({q['connection_id'] for q in qs}) and len({q['source'] for q in qs})==1;src=qs[0]['source'];budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs};cap=max(budgets.values())+1;fixed=bytes(base[n]-int(n in owners[net])<f['capacities'][n] for n in range(len(nodes)));(out/f'net{net}_allowed.bin').write_bytes(fixed);domains[net]=[]
 for mask in range(32):
  banned={n for i,n in enumerate(cut) if not mask>>i&1};d=[cap]*len(nodes);d[src]=min(cap,rc.initial(src)) if fixed[src] else cap;queue=[(d[src],src)] if d[src]<cap else []
  while queue:
   delay,u=heapq.heappop(queue)
   if d[u]!=delay:continue
   for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][edge]
    if not fixed[v] or v in banned:continue
    cost=min(cap,delay+rc.increments[edge])
    if cost<d[v]:d[v]=cost;heapq.heappush(queue,(cost,v))
  possible=all(d[q['sink']]<=budgets[q['connection_id']] for q in qs);file=out/f'net{net}_mask{mask}.bin';file.write_bytes(struct.pack('<'+str(len(nodes))+'Q',*d));rows.append(dict(net_id=net,mask=mask,cap=cap,budgets=budgets,queries=qs,sink_distances={q['connection_id']:d[q['sink']] for q in qs},possible_individual_paths=possible,certificate_file=str(file)))
  if possible:domains[net].append(mask)
 minimal[net]=[m for m in domains[net] if not any(k!=m and k&m==k for k in domains[net])];print('MASK DOMAIN',net,len(qs),minimal[net],flush=True)
result=pack_variants(f['capacities'],base,{net:[[n for i,n in enumerate(cut) if mask>>i&1] for mask in minimal[net]] for net in core},max_nodes=100000,deadline=time.perf_counter()+120);assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,core_nets=core,cut_nodes=cut,rows=rows,domains=domains,minimal_domains=minimal,result=result,total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');print('CUT MASKS',cut,result,flush=True)
