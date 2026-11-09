"""Whole-core shortest trees with fixed-owner removal proposals; never a route commit."""
import sys,json,time,heapq,itertools
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_budget_path_owner_release_v1_2026-10-07';out.mkdir();begin=time.perf_counter();diagnosis=R/'experiments/misex_net466_core_resource_masks_v1_2026-10-07';proof=diagnosis/'verification.json';pv=json.loads(proof.read_text());assert pv['necessary_capacity_obstruction_verified'];assert all(sha(k)==h for k,h in pv['bindings'].items());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';eventfile=R/'experiments/misex_net466_core_variant_expansion_v1_2026-10-07/event.json';bindings={**closure([Path(__file__)]),str(proof):sha(proof),str(ep):sha(ep),str(fp):sha(fp),str(eventfile):sha(eventfile)};bindings.update({row['path']:row['sha256'] for row in json.loads(ep.read_text())['inputs'].values()});cut=[16863,16903,21528,22625,22784];core=[258,384,466];release=[24,113,157,165,180,258,331,334,384];(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,core_nets=core,release=release,cut_nodes=cut,policy='All32 cut masks per core NET with fixed owners relaxed; reconstruct complete shortest-path trees in original RC budgets. Full-node cross-core capacity check. For each tree tuple, conservatively release every kept owner on overloaded nodes, then verify remaining kept plus all core trees capacity. Rank by extra owner count, released connection count, total physical edges; retain first12 tuples, maximum two per distinct expanded release scope. Proposal only; every extra owner and all originally released NETs must be fully restored before accepting2172CID candidate.'),indent=2)+'\n');graph,digest,nodes,f,rc,queries=load_endpoints(ep);qm={q['connection_id']:q for q in queries};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};event=json.loads(eventfile.read_text());groups=defaultdict(list);nodeowners=defaultdict(set);slots={edge:i for i,edge in enumerate(f['edge_ids'])};before=defaultdict(list)
for rec in event['before_records']:
 before[rec['net_id']].append(rec)
 if rec['net_id'] in core:groups[rec['net_id']].append(qm[rec['connection_id']])
 if rec['net_id'] not in release:
  for n in {rec['source']}|{f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids']}:nodeowners[n].add(rec['net_id'])
for q in event['selection']['queries']:groups[q['net_id']].append(q)
options={};attempts=[]
for net in core:
 qs=sorted(groups[net],key=lambda q:q['connection_id']);src=qs[0]['source'];assert len({q['source'] for q in qs})==1;budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs};cap=max(budgets.values())+1;options[net]=[];signatures=set()
 for mask in range(32):
  banned={n for i,n in enumerate(cut) if not mask>>i&1};d=[cap]*len(nodes);parent={};d[src]=min(cap,rc.initial(src));queue=[(d[src],src)] if f['capacities'][src] and d[src]<cap else []
  while queue:
   delay,u=heapq.heappop(queue)
   if d[u]!=delay:continue
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][slot]
    if not f['capacities'][v] or v in banned:continue
    candidate=min(cap,delay+rc.increments[slot])
    if candidate<d[v]:d[v]=candidate;parent[v]=(u,slot);heapq.heappush(queue,(candidate,v))
  possible=all(d[q['sink']]<=budgets[q['connection_id']] for q in qs);attempts.append(dict(net_id=net,mask=mask,all_original_queries_budget_feasible=possible))
  if not possible:continue
  records=[];own={src}
  for q in qs:
   v=q['sink'];path=[];seen={v};own.add(v)
   while v!=src:
    u,slot=parent[v];assert u not in seen;seen.add(u);own.add(u);path.append(f['edge_ids'][slot]);v=u
   path.reverse();assert rc.path(src,q['sink'],path)==d[q['sink']];records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=d[q['sink']]),budget_integer=budgets[q['connection_id']],floor_integer=floors[src,q['sink']]))
  sig=tuple(tuple(x['answer']['physical_edge_ids']) for x in records)
  if sig not in signatures:options[net].append(dict(mask=mask,records=records,nodes=sorted(own)));signatures.add(sig)
 print('Relaxed core trees',net,len(options[net]),flush=True)
proposals=[];counts=Counter()
for indices in itertools.product(*(range(len(options[n])) for n in core)):
 counts['tuples']+=1;chosen={n:options[n][i] for n,i in zip(core,indices)};ledger=Counter(n for op in chosen.values() for n in op['nodes'])
 if any(c>f['capacities'][n] for n,c in ledger.items()):counts['cross_core_capacity_reject']+=1;continue
 extras=sorted({owner for n,c in ledger.items() if c+len(nodeowners[n])>f['capacities'][n] for owner in nodeowners[n]});expanded=sorted(set(release)|set(extras));assert not set(extras).intersection(release);assert all(c+len(nodeowners[n]-set(extras))<=f['capacities'][n] for n,c in ledger.items());connections=sum(len(before[n]) for n in expanded)+len(event['selection']['queries']);edges=sum(len(x['answer']['physical_edge_ids']) for op in chosen.values() for x in op['records']);proposals.append(dict(extra_owners=extras,release=expanded,core_option_indices=dict(zip(core,indices)),restoration_connection_count=connections,total_core_physical_edges=edges));counts['full_core_with_necessary_owner_release']+=1
proposals.sort(key=lambda x:(len(x['extra_owners']),x['restoration_connection_count'],x['total_core_physical_edges'],x['extra_owners'],tuple(x['core_option_indices'].values())));selected=[];per_scope=Counter()
for p in proposals:
 scope=tuple(p['release'])
 if per_scope[scope]>=2:continue
 selected.append(p);per_scope[scope]+=1
 if len(selected)==12:break
(out/'event.json').write_text(json.dumps(event)+'\n');(out/'core_options.json').write_text(json.dumps(options)+'\n');(out/'proposals.json').write_text(json.dumps(selected,indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,attempts=attempts,counts=counts,selected_proposals=len(selected),total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');print('PROPOSALS',dict(counts),[(p['extra_owners'],p['restoration_connection_count']) for p in selected],flush=True)
