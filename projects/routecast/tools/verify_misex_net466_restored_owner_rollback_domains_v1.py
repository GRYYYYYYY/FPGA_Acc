"""Independent complete rollback enumeration, immutable seed and distance audit."""
import sys,json,struct
from pathlib import Path
from collections import defaultdict,Counter,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_restored_owner_rollback_domains_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());parent=R/'experiments/misex_net466_budget_path_owner_joint_v3_2026-10-07';prior=json.loads((parent/'receipt.json').read_text());pv=json.loads((parent/'branch_verification_dedup.json').read_text());pp=R/'experiments/misex_net466_budget_path_owner_release_v3_2026-10-07';event=json.loads((pp/'event.json').read_text());options={int(n):ops for n,ops in json.loads((pp/'core_options.json').read_text()).items()};proposals=json.loads((pp/'proposals.json').read_text());protected=set(json.loads((parent/'protocol.json').read_text())['protected_original_connection_ids']);_,_,nodes,f,rc,queries=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');assert all(x>=0 for x in rc.increments);qm={q['connection_id']:q for q in queries};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json').read_text())};slots={e:i for i,e in enumerate(f['edge_ids'])};assert len(r['rows'])==len(prior['attempts'])==8;certificates=0;arc_checks=0;results=[]
for row,a in zip(r['rows'],prior['attempts']):
 assert row['branch']==a['index'] and row['state_file']==a['state_file'] and bindings[a['state_file']]==pv['bindings'][a['state_file']];state=json.loads(Path(a['state_file']).read_text());q=state['failure']['query'];assert row['query']==q==qm[q['connection_id']];proposal=proposals[a['plan']['proposal_index']];seed=[x for x in event['before_records'] if x['net_id'] not in proposal['release'] or x['connection_id'] in protected]+[x for n,i in proposal['core_option_indices'].items() for x in options[int(n)][i]['records']];seedmap={x['connection_id']:x for x in seed};actual={x['connection_id']:x for x in state['records']};assert len(actual)==len(state['records']) and all(actual[c]==x for c,x in seedmap.items());mutable=defaultdict(set)
 for cid,rec in actual.items():
  if cid not in seedmap and rec['net_id']!=q['net_id']:mutable[rec['net_id']].add(cid)
 assert len(row['checks'])==len(mutable) and {x['rollback_net'] for x in row['checks']}==set(mutable);budget=max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2);assert row['budget']==budget;cap=budget+1
 for check in row['checks']:
  certificates+=1;net=check['rollback_net'];removed=set(check['removed_connection_ids']);assert removed==mutable[net] and not removed.intersection(seedmap);kept={cid:x for cid,x in actual.items() if cid not in removed};assert all(kept[c]==x for c,x in seedmap.items());owners=defaultdict(set)
  for rec in kept.values():owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
  other=Counter(n for nset in (s for owner,s in owners.items() if owner!=q['net_id']) for n in nset);allowed=bytes(other[n]<f['capacities'][n] for n in range(len(nodes)));assert Path(check['allowed_file']).read_bytes()==allowed;raw=Path(check['certificate_file']).read_bytes();assert len(raw)==8*len(nodes);d=struct.unpack('<'+str(len(nodes))+'Q',raw);assert all(x<=cap for x in d);assert d[q['source']]==(min(cap,rc.initial(q['source'])) if allowed[q['source']] else cap)
  for u in range(len(nodes)):
   if not allowed[u]:assert d[u]==cap;continue
   if d[u]==cap:arc_checks+=f['row_offsets'][u+1]-f['row_offsets'][u];continue
   for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][edge]
    if allowed[v]:assert d[v]<=min(cap,d[u]+rc.increments[edge]);arc_checks+=1
  reached={q['source']} if allowed[q['source']] and d[q['source']]<cap else set();queue=deque(reached)
  while queue:
   u=queue.popleft()
   for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][edge]
    if allowed[v] and v not in reached and d[v]<cap and d[v]==d[u]+rc.increments[edge]:reached.add(v);queue.append(v)
  assert reached=={n for n,x in enumerate(d) if x<cap};assert check['minimum_capped_delay']==d[q['sink']];feasible=d[q['sink']]<=budget;assert check['budget_feasible']==feasible
  if feasible:
   path=check['physical_edge_ids'];assert rc.path(q['source'],q['sink'],path)==d[q['sink']];u=q['source'];assert allowed[u]
   for eid in path:slot=slots[eid];assert f['row_offsets'][u]<=slot<f['row_offsets'][u+1];u=f['dest_ranks'][slot];assert allowed[u]
   assert u==q['sink']
  else:assert check['physical_edge_ids'] is None
 ordered=sorted((c for c in row['checks'] if c['budget_feasible']),key=lambda c:(len(c['removed_connection_ids']),c['minimum_capped_delay'],c['rollback_net']));assert row['ranked_feasible_rollback_nets']==[c['rollback_net'] for c in ordered];results.append(dict(branch=row['branch'],probes=len(row['checks']),feasible_rollback_nets=row['ranked_feasible_rollback_nets']));print('PASS rollback domains',row['branch'],row['ranked_feasible_rollback_nets'],flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=results,immutable_seed_and_complete_mutable_net_enumeration_pass=True,exact_capped_distance_certificates=certificates,all_arc_inequalities_including_tautologies=arc_checks,scope='Rollback every mutable record of one other NET; immutable initialseed preserved. Feasible individual paths are repair-domain suggestions, not actual joint route restoration or commit; single-owner exhaustion does not exclude multi-owner repair/native routes.'),indent=2)+'\n');print('PASS rollback enumeration',certificates,flush=True)
