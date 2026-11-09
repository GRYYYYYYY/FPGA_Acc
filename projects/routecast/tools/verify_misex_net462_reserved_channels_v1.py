"""Independent complete-query mask potentials, attainability and capacity audit."""
import sys,json,struct,itertools
from pathlib import Path
from collections import defaultdict,Counter,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_net462_reserved_channels_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());parent=R/'experiments/misex_net466_expanded_tree_pool_v3_2026-10-07';pv=json.loads((parent/'verification.json').read_text());core=sorted(int(n) for n in json.loads((parent/'protocol.json').read_text())['groups']);assert core==r['core_nets']==p['core_nets'];ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';_,_,nodes,f,rc,queries=load_endpoints(ep);qm={q['connection_id']:q for q in queries};assert all(x>=0 for x in rc.increments);seed=json.loads((parent/'seed.json').read_text());pp=json.loads((parent/'protocol.json').read_text());pool={int(n):ops for n,ops in json.loads((parent/'pool.json').read_text()).items()};slots={e:i for i,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in seed:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
base=Counter(n for s in owners.values() for n in s);groups={n:pp['groups'][str(n)]+[{k:x[k] for k in ['connection_id','net_id','source','sink']} for x in seed if x['net_id']==n] for n in core};assert p['groups']=={str(n):qs for n,qs in groups.items()};protected={q[k] for qs in groups.values() for q in qs for k in ['source','sink']};occ={n:Counter(node for op in pool[n] for node in op['nodes']) for n in core};scores={n:sum(occ[a][n]*occ[b][n] for i,a in enumerate(core) for b in core[i+1:]) for n in set().union(*(set(c) for c in occ.values()))};reservation=R/'experiments/misex_net462_channel_necessity_v1_2026-10-07';rv=json.loads((reservation/'verification.json').read_text());rrp=reservation/'receipt.json';assert sha(rrp)==rv['bindings'][str(rrp)];rr=json.loads(rrp.read_text());cut=rr['original_channel_nodes'];assert all(f['capacities'][n]==1 and not base[n] for n in cut);assert all(not next(row for row in rr['rows'] if row['context']=='exact_seed' and row['banned_nodes']==[n])['budget_feasible'] for n in cut);assert sha(parent/'seed.json')==rv['bindings'][str(parent/'seed.json')];assert cut==r['cut_nodes']==p['cut_nodes'];floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};assert len(r['rows'])==len(core) and {(x['net_id'],x['mask']) for x in r['rows']}=={(n,15 if n==462 else 0) for n in core};domains=defaultdict(list);checks=0
for row in r['rows']:
 net=row['net_id'];qs=sorted(groups[net],key=lambda q:q['connection_id']);assert qs==row['queries'] and all(q==qm[q['connection_id']] for q in qs) and len({q['source'] for q in qs})==1;src=qs[0]['source'];budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs};cap=max(budgets.values())+1;assert row['cap']==cap and row['budgets']=={str(c):b for c,b in budgets.items()};fixed=bytes(base[n]-int(n in owners[net])<f['capacities'][n] for n in range(len(nodes)));assert (out/f'net{net}_allowed.bin').read_bytes()==fixed;banned={n for i,n in enumerate(cut) if not row['mask']>>i&1};allowed=[bool(fixed[n]) and n not in banned for n in range(len(nodes))];raw=Path(row['certificate_file']).read_bytes();assert len(raw)==8*len(nodes);d=struct.unpack('<'+str(len(nodes))+'Q',raw);assert all(v<=cap for v in d);assert d[src]==(min(cap,rc.initial(src)) if allowed[src] else cap)
 for u in range(len(nodes)):
  if not allowed[u]:assert d[u]==cap;continue
  if d[u]==cap:checks+=f['row_offsets'][u+1]-f['row_offsets'][u];continue
  for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][edge]
   if allowed[v]:assert d[v]<=min(cap,d[u]+rc.increments[edge]);checks+=1
 reached={src} if allowed[src] and d[src]<cap else set();queue=deque(reached)
 while queue:
  u=queue.popleft()
  for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][edge]
   if allowed[v] and v not in reached and d[v]<cap and d[v]==d[u]+rc.increments[edge]:reached.add(v);queue.append(v)
 assert reached=={n for n,x in enumerate(d) if x<cap};assert row['sink_distances']=={str(q['connection_id']):d[q['sink']] for q in qs};possible=all(d[q['sink']]<=budgets[q['connection_id']] for q in qs);assert possible==row['possible_individual_paths']
 if possible:domains[net].append(row['mask'])
domains.update({n:domains[n] for n in core});minimal={n:[m for m in domains[n] if not any(k!=m and k&m==k for k in domains[n])] for n in core};assert {str(n):m for n,m in domains.items()}==r['domains'] and {str(n):m for n,m in minimal.items()}==r['minimal_domains'];tested=0;witness=None
for masks in itertools.product(*(minimal[n] for n in core)):
 tested+=1
 if all(base[n]+sum(bool(mask>>i&1) for mask in masks)<=f['capacities'][n] for i,n in enumerate(cut)):witness=dict(zip(core,masks));break
result=r['result']
if witness is None:assert result['status']=='POOL_EXHAUSTED'
else:
 assert result['status']=='FOUND_POOL_BATCH';selected={int(n):minimal[int(n)][i] for n,i in result['chosen_option_indices'].items()};assert set(selected)==set(core);assert all(base[n]+sum(bool(m>>i&1) for m in selected.values())<=f['capacities'][n] for i,n in enumerate(cut))
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,exact_capped_certificates=len(r['rows']),core_query_counts={n:len(qs) for n,qs in groups.items()},all_arc_inequalities_including_tautologies=checks,independent_mask_combinations_tested=tested,compatible_mask_witness=witness,necessary_cut_capacity_obstruction=witness is None,scope='All fiveNET original queries, same seed, exact RC domains with tree/other mutable NETs relaxed. Compatible masks inconclusive, not accepted trees; obstruction only for this seed/model, never native/global/QoR/workflow proof.'),indent=2)+'\n');print('PASS expanded core masks',witness,tested,checks,flush=True)
