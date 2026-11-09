"""Independent exact distance certificates and complete restored-query gate audit."""
import sys,json,struct
from pathlib import Path
from collections import defaultdict,Counter,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_owner_restoration_viability_v2_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());assert p['bindings']==r['bindings'];ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';_,_,nodes,f,rc,queries=load_endpoints(ep);assert all(c>=0 for c in rc.increments);qm={q['connection_id']:q for q in queries};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};slots={e:i for i,e in enumerate(f['edge_ids'])};parents={};expectedcases=set();checks=0;nontrivial=0;certificates=0;coverage=0;proofrows=[]
for source in p['sources']:
 version=source['version'];parent=Path(source['parent']);pv=json.loads((parent/'verification.json').read_text());assert pv['whole_net_owner_release_and_fixed_seed_plus_core_capacity_pass'];
 for name in ['event.json','core_options.json','proposals.json']:assert pv['bindings'][str(parent/name)]==bindings[str(parent/name)]
 event=json.loads((parent/'event.json').read_text());options={int(n):ops for n,ops in json.loads((parent/'core_options.json').read_text()).items()};proposals=json.loads((parent/'proposals.json').read_text());parents[version]=(event,options,proposals);expectedcases.update((version,i) for i in range(len(proposals)))
assert len(r['cases'])==len(expectedcases) and {(x['version'],x['proposal_index']) for x in r['cases']}==expectedcases
for case in r['cases']:
 event,options,proposals=parents[case['version']];proposal=proposals[case['proposal_index']];assert proposal['release']==case['release'];kept=[x for x in event['before_records'] if x['net_id'] not in case['release']];core_records=[x for n,i in proposal['core_option_indices'].items() for x in options[int(n)][i]['records']];seed=kept+core_records;assert len({x['connection_id'] for x in seed})==len(seed);owners=defaultdict(set)
 for rec in seed:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
 occupancy=Counter(n for own in owners.values() for n in own);assert all(c<=f['capacities'][n] for n,c in occupancy.items());allowed=bytes(occupancy[n]<f['capacities'][n] for n in range(len(nodes)));assert Path(case['allowed_file']).read_bytes()==allowed;groups=defaultdict(dict)
 for rec in event['before_records']:
  if rec['net_id'] in case['release'] and rec['net_id'] not in options:groups[rec['net_id']][rec['connection_id']]=qm[rec['connection_id']]
 assert len(case['rows'])==len(groups) and {x['net_id'] for x in case['rows']}==set(groups);assert len(seed)==case['seed_connections'] and sum(len(g) for g in groups.values())==case['restoration_connections'];assert len(seed)+case['restoration_connections']==2172;allfail=[]
 for row in case['rows']:
  certificates+=1;net=row['net_id'];qs=sorted(groups[net].values(),key=lambda q:q['connection_id']);assert qs==row['queries'] and len({q['source'] for q in qs})==1 and net not in owners;src=qs[0]['source'];budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs};cap=max(budgets.values())+1;assert row['cap']==cap and row['budgets']=={str(k):v for k,v in budgets.items()};file=Path(row['certificate_file']);assert sha(file)==row['certificate_sha256'];raw=file.read_bytes();assert len(raw)==len(nodes)*8;d=struct.unpack('<'+str(len(nodes))+'Q',raw);assert all(v<=cap for v in d);assert d[src]==(min(cap,rc.initial(src)) if allowed[src] else cap)
  for u in range(len(nodes)):
   if not allowed[u]:assert d[u]==cap;continue
   if d[u]==cap:
    # Every target is <=cap and all increments are nonnegative: capped inequalities are tautologies.
    checks+=f['row_offsets'][u+1]-f['row_offsets'][u];continue
   for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][edge]
    if allowed[v]:assert d[v]<=min(cap,d[u]+rc.increments[edge]);checks+=1;nontrivial+=1
  reached={src} if allowed[src] and d[src]<cap else set();queue=deque(reached)
  while queue:
   u=queue.popleft()
   for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][edge]
    if allowed[v] and v not in reached and d[v]<cap and d[v]==d[u]+rc.increments[edge]:reached.add(v);queue.append(v)
  assert reached=={n for n,x in enumerate(d) if x<cap};failed=[q['connection_id'] for q in qs if d[q['sink']]>budgets[q['connection_id']]];assert failed==row['failed_budget_connection_ids'] and row['sink_distances']=={str(q['connection_id']):d[q['sink']] for q in qs};allfail.extend(failed);coverage+=len(qs)
 assert case['necessary_gate_pass']==(not allfail);proofrows.append(dict(version=case['version'],proposal_index=case['proposal_index'],restoration_queries_verified=case['restoration_connections'],failed_queries=len(allfail),gate_pass=not allfail));print('PASS gate case',case['version'],case['proposal_index'],len(allfail),flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,cases=proofrows,exact_capped_shortest_certificates=certificates,restoration_query_instances_verified=coverage,all_arc_inequalities_including_cap_tautologies=checks,explicit_nontrivial_arc_checks=nontrivial,all_complete_scope_fixed_seed_and_budget_checks_pass=True,scope='Exact individual budget reachability against frozen seed. Any failure rejects that seed independent of restoration order; gate pass alone cannot certify joint trees/capacity. No negative claim about other core trees or native/QoR/heldout/workflow performance.'),indent=2)+'\n');print('PASS complete restoration gate',certificates,coverage,checks,flush=True)
