"""Build full alternative shortest trees from certified tight edges, then recombine all NETs."""
import sys,json,time,struct
from pathlib import Path
from collections import defaultdict,Counter,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from tree_variant_capacity_packing_v1 import pack_variants
out=R/'experiments/misex_net466_expanded_tree_pool_v2_2026-10-07';out.mkdir();begin=time.perf_counter();parent=R/'experiments/misex_net466_expanded_tree_pool_v1_2026-10-07';masks=R/'experiments/misex_net466_expanded_core_masks_v1_2026-10-07';vp=parent/'verification.json';pv=json.loads(vp.read_text());gp=masks/'verification.json';gv=json.loads(gp.read_text());assert not gv['necessary_cut_capacity_obstruction'];mr=masks/'receipt.json';assert sha(mr)==gv['bindings'][str(mr)];m=json.loads(mr.read_text());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(vp):sha(vp),str(gp):sha(gp),str(mr):sha(mr),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()})
for name in ['seed.json','event.json','protocol.json','pool.json']:bindings[str(parent/name)]=sha(parent/name);assert pv['bindings'][str(parent/name)]==bindings[str(parent/name)]
p=json.loads((parent/'protocol.json').read_text());seed=json.loads((parent/'seed.json').read_text());groups={int(n):qs for n,qs in p['groups'].items()};pools={int(n):ops for n,ops in json.loads((parent/'pool.json').read_text()).items()};_,_,nodes,f,rc,queries=load_endpoints(ep);slots={e:i for i,e in enumerate(f['edge_ids'])};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};seedowners=defaultdict(set)
def own(records):return {x['source'] for x in records}|{f['dest_ranks'][slots[e]] for x in records for e in x['answer']['physical_edge_ids']}
for rec in seed:seedowners[rec['net_id']].update(own([rec]))
base=Counter(n for s in seedowners.values() for n in s);generated=[]
for netstr,mask in gv['compatible_mask_witness'].items():
 net=int(netstr);assert not seedowners[net],'Current fixture requires no immutable sameNET tree; otherwise tight-tree construction must honor its parents';row=next(x for x in m['rows'] if x['net_id']==net and x['mask']==mask);file=Path(row['certificate_file']);bindings[str(file)]=sha(file);assert bindings[str(file)]==gv['bindings'][str(file)];d=struct.unpack('<'+str(len(nodes))+'Q',file.read_bytes());cap=row['cap'];banned={n for i,n in enumerate(m['cut_nodes']) if not mask>>i&1};allowed=bytes(base[n]<f['capacities'][n] and n not in banned for n in range(len(nodes)));src=row['queries'][0]['source'];parents={};reached={src};queue=deque([src])
 while queue:
  u=queue.popleft()
  for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][edge]
   if allowed[v] and v not in reached and d[v]<cap and d[v]==d[u]+rc.increments[edge]:reached.add(v);parents[v]=(u,edge);queue.append(v)
 assert reached=={n for n,x in enumerate(d) if x<cap};records=[]
 for q in sorted(groups[net],key=lambda q:q['connection_id']):
  u=q['sink'];assert u in reached;path=[]
  while u!=src:pnode,edge=parents[u];path.append(f['edge_ids'][edge]);u=pnode
  path.reverse();floor=floors[src,q['sink']];budget=max(rc.scale//10**9,(3*floor+1)//2);assert rc.path(src,q['sink'],path)==d[q['sink']]<=budget;records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=d[q['sink']]),budget_integer=budget,floor_integer=floor))
 statefile=out/f'generated_net{net}.json';statefile.write_text(json.dumps(dict(records=records,failure=None,seed_file=str(out/'seed.json'),certificate_file=str(file),mask=mask))+'\n');sig=tuple((x['connection_id'],tuple(x['answer']['physical_edge_ids'])) for x in records);old={tuple((x['connection_id'],tuple(x['answer']['physical_edge_ids'])) for x in op['records']) for op in pools[net]};added=sig not in old
 if added:pools[net].append(dict(records=records,nodes=sorted(own(records)-seedowners[net]),origin=str(statefile)))
 generated.append(dict(net_id=net,mask=mask,added_variant=added,connections=len(records)));print('CERTIFIED TREE',net,mask,len(records),added,flush=True)
(out/'seed.json').write_text(json.dumps(seed)+'\n');(out/'event.json').write_text((parent/'event.json').read_text());(out/'pool.json').write_text(json.dumps(pools)+'\n');(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,groups=groups,search_seconds=120,max_nodes=100000,generated=generated,policy='Original232 complete variants plus shortest trees from certified compatible resource-mask tight edges; node choices subtract only same NET seed-owned nodes so protected trunk charged once, other NET seed occupancy remains. All27groups/full2172CID required, compact paths with immutable seed. Finite pooling only, no all-path/native proof.'),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());start=time.perf_counter();result=pack_variants(f['capacities'],base,{n:[op['nodes'] for op in ops] for n,ops in pools.items()},max_nodes=100000,deadline=start+120);solution=None
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
