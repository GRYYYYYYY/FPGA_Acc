"""Independent all-arc potentials, tight-path attainability and Cartesian cut audit."""
import sys,json,struct,itertools
from pathlib import Path
from collections import defaultdict,Counter,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_core_resource_masks_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items()) and p['bindings']==r['bindings'];parent=R/'experiments/misex_net466_core_variant_expansion_v1_2026-10-07';pv=json.loads((parent/'generation_and_palette_verification.json').read_text());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json'
for path in [ep,fp,parent/'event.json']:assert pv['bindings'][str(path)]==bindings[str(path)]
assert r['core_nets']==p['core_nets']==[258,384,466] and r['release']==p['release']==[24,113,157,165,180,258,331,334,384] and r['cut_nodes']==p['cut_nodes']==[16863,16903,21528,22625,22784];_,_,nodes,f,rc,queries=load_endpoints(ep);qm={q['connection_id']:q for q in queries};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};event=json.loads((parent/'event.json').read_text());groups=defaultdict(dict);owners=defaultdict(set);slots={e:i for i,e in enumerate(f['edge_ids'])}
for rec in event['before_records']:
 if rec['net_id'] in r['core_nets']:groups[rec['net_id']][rec['connection_id']]=qm[rec['connection_id']]
 if rec['net_id'] not in r['release']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
for q in event['selection']['queries']:assert q==qm[q['connection_id']] and q['connection_id'] not in groups[q['net_id']];groups[q['net_id']][q['connection_id']]=q
base=Counter(n for own in owners.values() for n in own);fixed=bytes(base[n]<f['capacities'][n] for n in range(len(nodes)));assert fixed==(out/'fixed_allowed.bin').read_bytes();assert all(base[n]<=f['capacities'][n] for n in base);cut=r['cut_nodes'];assert len(r['rows'])==96 and {(x['net_id'],x['mask']) for x in r['rows']}==set(itertools.product(r['core_nets'],range(32)));domains=defaultdict(list);arcs=0;tightnodes=0
for row in r['rows']:
 net=row['net_id'];qs=sorted(groups[net].values(),key=lambda q:q['connection_id']);assert row['queries']==qs and len({q['source'] for q in qs})==1;source=qs[0]['source'];budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs};cap=max(budgets.values())+1;assert row['cap']==cap and row['budgets']=={str(k):v for k,v in budgets.items()};banned={n for i,n in enumerate(cut) if not row['mask']>>i&1};allowed=[bool(fixed[n]) and n not in banned for n in range(len(nodes))];assert source not in cut and all(q['sink'] not in cut for q in qs);file=Path(row['certificate_file']);assert sha(file)==row['certificate_sha256'];raw=file.read_bytes();assert len(raw)==len(nodes)*8;d=struct.unpack('<'+str(len(nodes))+'Q',raw);assert all(0<=v<=cap for v in d);assert d[source]==(min(rc.initial(source),cap) if allowed[source] else cap)
 for u in range(len(nodes)):
  if not allowed[u]:assert d[u]==cap;continue
  for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][edge]
   if allowed[v]:assert d[v]<=min(cap,d[u]+rc.increments[edge]);arcs+=1
 # Reachability in the equality graph supplies paths attaining every finite potential.
 reached={source} if allowed[source] and d[source]<cap else set();queue=deque(reached)
 while queue:
  u=queue.popleft()
  for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][edge]
   if v not in reached and allowed[v] and d[v]<cap and d[v]==d[u]+rc.increments[edge]:reached.add(v);queue.append(v)
 assert reached=={n for n,value in enumerate(d) if value<cap};tightnodes+=len(reached);possible=all(d[q['sink']]<=budgets[q['connection_id']] for q in qs);assert possible==row['possible_individual_paths'] and row['sink_distances']=={str(q['connection_id']):d[q['sink']] for q in qs}
 if possible:domains[net].append(row['mask'])
print('PASS exact masked distances',len(r['rows']),arcs,flush=True)
assert {str(n):sorted(domains[n]) for n in r['core_nets']}==r['domains'];combinations=[];tested=0
for values in itertools.product(*(sorted(domains[n]) for n in r['core_nets'])):
 tested+=1
 if all(base[n]+sum(bool(mask>>i&1) for mask in values)<=f['capacities'][n] for i,n in enumerate(cut)):combinations.append({str(n):mask for n,mask in zip(r['core_nets'],values)})
assert tested==r['combinations_tested'] and combinations==r['compatible_mask_combinations'] and r['necessary_capacity_obstruction']==(not combinations);assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,core_query_counts={n:len(groups[n]) for n in r['core_nets']},masked_shortest_distance_certificates=96,all_arc_inequalities=arcs,tight_path_nodes_verified=tightnodes,compatible_mask_combinations=len(combinations),necessary_capacity_obstruction_verified=r['necessary_capacity_obstruction'],scope='All original core connections covered. Exact individual shortest paths plus complete cut-capacity enumeration; masks relax single-parent trees and other released NETs. Compatible masks are inconclusive and never accepted routes; no native QoR or workflow claim.'),indent=2)+'\n');print('PASS resource masks',tested,len(combinations),flush=True)
