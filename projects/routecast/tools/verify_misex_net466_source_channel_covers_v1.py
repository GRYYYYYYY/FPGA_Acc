"""Independent source-prefix relaxation, distance certificates and exhaustive covers."""
import sys,json,struct,itertools,time
from pathlib import Path
from collections import defaultdict,Counter,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
begin=time.perf_counter();out=R/'experiments/misex_net466_source_channel_covers_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());assert r['bindings']==p['bindings'];bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items())
parent=R/'experiments/misex_net466_expanded_tree_pool_v4_2026-10-07';pv=json.loads((parent/'verification.json').read_text());seed=json.loads((parent/'seed.json').read_text());pp=json.loads((parent/'protocol.json').read_text());necessity=R/'experiments/misex_net462_channel_necessity_v1_2026-10-07';nr=json.loads((necessity/'receipt.json').read_text());nv=json.loads((necessity/'verification.json').read_text());assert nv['all_original_channel_probes_scope_and_physical_witnesses_pass'];assert nv['bindings'][str(necessity/'receipt.json')]==sha(necessity/'receipt.json');reserved=nr['original_channel_nodes'];assert reserved==p['reserved_for_net462'];assert all(not next(x for x in nr['rows'] if x['context']=='exact_seed' and x['banned_nodes']==[n])['budget_feasible'] for n in reserved);assert sha(parent/'seed.json')==nv['bindings'][str(R/'experiments/misex_net466_expanded_tree_pool_v3_2026-10-07/seed.json')]
core=sorted(n for n in pv['proof']['core_nets'] if n!=462);assert sorted(p['core_nets'])==core;assert sorted(x['net_id'] for x in r['rows'])==core
_,_,nodes,f,rc,queries=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');assert all(x>=0 for x in rc.increments);channel=[x.get('type') in ('CHANX','CHANY') for x in nodes];slots={e:i for i,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in seed:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
base=Counter(n for owned in owners.values() for n in owned);assert all(f['capacities'][n]==1 and base[n]==0 for n in reserved);capacity_base=Counter(base);capacity_base.update(reserved);assert all(c<=f['capacities'][n] for n,c in capacity_base.items());floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json').read_text())};original={q['connection_id']:q for q in queries};options={};checks=certificates=query_count=0
for row in r['rows']:
 net=row['net_id'];qs=sorted(pp['groups'][str(net)]+[{k:x[k] for k in ('connection_id','net_id','source','sink')} for x in seed if x['net_id']==net],key=lambda q:q['connection_id']);assert qs==sorted(p['groups'][str(net)],key=lambda q:q['connection_id']);assert len({q['connection_id'] for q in qs})==len(qs);assert all(q==original[q['connection_id']] for q in qs);assert len({q['source'] for q in qs})==1;src=qs[0]['source'];budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs};cap=max(budgets.values())+1;assert row['cap']==cap
 allowed=bytes(base[n]-int(n in owners[net])<f['capacities'][n] and n not in reserved for n in range(len(nodes)));assert allowed==(out/f'net{net}/allowed.bin').read_bytes()
 # FIFO label correction independently computes the non-channel prefix closure.
 prefix={src:rc.initial(src)} if allowed[src] and rc.initial(src)<cap else {};queue=deque(prefix);queued=set(prefix);first={}
 while queue:
  u=queue.popleft();queued.remove(u)
  for e in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][e];cost=prefix[u]+rc.increments[e]
   if not allowed[v] or cost>=cap:continue
   if channel[v]:first[v]=min(first.get(v,cap),cost)
   elif cost<prefix.get(v,cap):
    prefix[v]=cost
    if v not in queued:queued.add(v);queue.append(v)
 assert prefix=={int(k):v for k,v in row['prefix'].items()};assert first=={int(k):v for k,v in row['first_prefix_delays'].items()};starts=sorted(first);assert starts==row['starts'];assert len(row['certificates'])==len(starts);assert sorted(x['first_channel'] for x in row['certificates'])==starts;fields={}
 for cert in row['certificates']:
  start=cert['first_channel'];assert cert['source_prefix_delay']==first[start];file=out/f'net{net}/first{start}.bin';assert Path(cert['file'])==file and str(file) in r['files'];raw=file.read_bytes();assert len(raw)==8*len(nodes);d=struct.unpack('<'+str(len(nodes))+'Q',raw);assert all(x<=cap for x in d);assert d[start]==first[start]
  for u in range(len(nodes)):
   if not allowed[u]:assert d[u]==cap;continue
   if d[u]==cap:checks+=f['row_offsets'][u+1]-f['row_offsets'][u];continue
   for e in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][e]
    if allowed[v]:assert d[v]<=min(cap,d[u]+rc.increments[e]);checks+=1
  reached={start};queue=deque([start])
  while queue:
   u=queue.popleft()
   for e in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][e]
    if allowed[v] and v not in reached and d[v]<cap and d[v]==d[u]+rc.increments[e]:reached.add(v);queue.append(v)
  assert reached=={n for n,x in enumerate(d) if x<cap};fields[start]=d;certificates+=1
 domains=[dict(query=q,budget=budgets[q['connection_id']],no_channel_path=prefix.get(q['sink'],cap)<=budgets[q['connection_id']],first_channel_domain=[n for n in starts if fields[n][q['sink']]<=budgets[q['connection_id']]]) for q in qs];assert domains==row['domains'];mandatory=set()
 for rec in seed:
  if rec['net_id']==net:
   for eid in rec['answer']['physical_edge_ids']:
    n=f['dest_ranks'][slots[eid]]
    if channel[n]:mandatory.add(n);break
 assert sorted(mandatory)==row['immutable_first_channels'];covers=[]
 for mask in range(1<<len(starts)):
  selected={n for i,n in enumerate(starts) if mask>>i&1}
  if mandatory<=selected and all(x['no_channel_path'] or selected.intersection(x['first_channel_domain']) for x in domains):covers.append(mask)
 minimal=[m for m in covers if not any(other!=m and other&m==other for other in covers)];assert len(covers)==row['all_cover_count'] and minimal==row['minimal_cover_masks'];options[net]=[[n for i,n in enumerate(starts) if m>>i&1 and n not in owners[net]] for m in minimal];assert options[net]==row['cover_node_increments'];query_count+=len(qs);print('PASS covers',net,len(qs),len(starts),len(minimal),flush=True)
# Exhaustive Cartesian allocation, independently of the producer's MRV packing.
compatible=0;witness=None;tested=0
for choice in itertools.product(*(range(len(options[n])) for n in core)):
 tested+=1;counts=Counter(capacity_base)
 for n,i in zip(core,choice):counts.update(options[n][i])
 if all(c<=f['capacities'][n] for n,c in counts.items()):
  compatible+=1
  if witness is None:witness=dict(zip(core,choice))
assert r['result']['status']==('FOUND_POOL_BATCH' if compatible else 'POOL_EXHAUSTED')
if compatible:
 selected={int(n):i for n,i in r['result']['chosen_option_indices'].items()};assert sorted(selected)==core;counts=Counter(capacity_base)
 for n,i in selected.items():assert 0<=i<len(options[n]);counts.update(options[n][i])
 assert all(c<=f['capacities'][n] for n,c in counts.items())
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,source_prefix_fifo_verified=True,exact_capped_budget_walk_certificates=certificates,all_arc_inequalities_including_tautologies=checks,full_query_instances=query_count,all_cover_subsets_and_minimal_antichains_verified=True,cartesian_allocations_tested=tested,compatible_allocations=compatible,independent_witness=witness,producer_selected_capacity_verified=bool(compatible),paid_verification_seconds=time.perf_counter()-begin,scope='Necessary source-channel budget-walk cover relaxation only. Internal occupancy, simple path constraints and joint tree parents are relaxed. Compatible covers do not certify a full route, nativeQoR or workflow gain.'),indent=2)+'\n');print('PASS source covers',certificates,query_count,tested,compatible,flush=True)
