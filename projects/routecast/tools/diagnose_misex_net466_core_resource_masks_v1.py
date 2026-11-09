"""Necessary whole-NET resource-mask domains from all original per-connection budgets."""
import sys,json,time,heapq,struct,itertools
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_core_resource_masks_v1_2026-10-07';out.mkdir();begin=time.perf_counter();parent=R/'experiments/misex_net466_core_variant_expansion_v1_2026-10-07';proof=parent/'generation_and_palette_verification.json';pv=json.loads(proof.read_text());assert pv['all_original_budgets_seed_preservation_tree_and_caps_pass'];ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';eventfile=parent/'event.json';bindings={**closure([Path(__file__)]),str(proof):sha(proof),str(eventfile):sha(eventfile),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({row['path']:row['sha256'] for row in json.loads(ep.read_text())['inputs'].values()});assert all(sha(k)==h for k,h in bindings.items());cut=[16863,16903,21528,22625,22784];core=[258,384,466];release=[24,113,157,165,180,258,331,334,384];(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cut_nodes=cut,core_nets=core,release=release,policy='All32 allowed masks for each core NET; all original core connections including all5 target requests, original additive RC budgets. Forward capped shortest distances with exact fixed-kept capacity bans. Enumerate mask combinations for capacity. Relax other released NETs and tree-parent compatibility only for necessary-condition diagnosis; never accept as routed candidate.',scope='Post-outcome coupled resource-domain diagnosis; a compatible domain tuple is inconclusive, absence proves only fixed-kept additive-model cut obstruction, not native/global placement impossibility.'),indent=2)+'\n');graph,digest,nodes,f,rc,queries=load_endpoints(ep);qm={q['connection_id']:q for q in queries};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};event=json.loads(eventfile.read_text());groups=defaultdict(list);owners=defaultdict(set);slots={edge:i for i,edge in enumerate(f['edge_ids'])}
for rec in event['before_records']:
 if rec['net_id'] in core:groups[rec['net_id']].append(qm[rec['connection_id']])
 if rec['net_id'] not in release:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
for q in event['selection']['queries']:assert q['net_id'] in core;groups[q['net_id']].append(q)
base=Counter(n for own in owners.values() for n in own);allowed=bytes(base[n]<f['capacities'][n] for n in range(len(nodes)));(out/'fixed_allowed.bin').write_bytes(allowed);rows=[];domains={};cutset=set(cut)
for net in core:
 qs=sorted(groups[net],key=lambda q:q['connection_id']);assert len({q['source'] for q in qs})==1;source=qs[0]['source'];budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs};cap=max(budgets.values())+1;assert source not in cutset and all(q['sink'] not in cutset for q in qs);domains[net]=[]
 for mask in range(1<<len(cut)):
  banned={n for i,n in enumerate(cut) if not mask>>i&1};dist=[cap]*len(nodes);dist[source]=min(cap,rc.initial(source)) if allowed[source] else cap;queue=[(dist[source],source)] if dist[source]<cap else []
  while queue:
   delay,u=heapq.heappop(queue)
   if dist[u]!=delay:continue
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][slot]
    if not allowed[v] or v in banned:continue
    cost=min(cap,delay+rc.increments[slot])
    if cost<dist[v]:dist[v]=cost;heapq.heappush(queue,(cost,v))
  possible=all(dist[q['sink']]<=budgets[q['connection_id']] for q in qs);file=out/f'net{net}_mask{mask}.bin';file.write_bytes(struct.pack('<'+str(len(nodes))+'Q',*dist));rows.append(dict(net_id=net,mask=mask,queries=qs,budgets=budgets,cap=cap,possible_individual_paths=possible,sink_distances={q['connection_id']:dist[q['sink']] for q in qs},certificate_file=str(file),certificate_sha256=sha(file)))
  if possible:domains[net].append(mask)
 print('NET masks',net,len(qs),domains[net],flush=True)
compatible=[];tested=0
for masks in itertools.product(*(domains[n] for n in core)):
 tested+=1;counts=Counter(n for mask in masks for i,n in enumerate(cut) if mask>>i&1)
 if all(base[n]+counts[n]<=f['capacities'][n] for n in cut):compatible.append(dict(zip(core,masks)))
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,core_nets=core,release=release,cut_nodes=cut,rows=rows,domains=domains,combinations_tested=tested,compatible_mask_combinations=compatible,necessary_capacity_obstruction=not compatible,total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');print('MASK RESULT',tested,len(compatible),flush=True)
