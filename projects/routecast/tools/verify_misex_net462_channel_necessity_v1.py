"""Independent exhaustive channel probes, exact RC certificates and physical witnesses."""
import sys,json,struct
from pathlib import Path
from collections import defaultdict,Counter,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net462_channel_necessity_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());parent=R/'experiments/misex_net466_expanded_tree_pool_v3_2026-10-07';seed=json.loads((parent/'seed.json').read_text());pool=json.loads((parent/'pool.json').read_text());_,_,nodes,f,rc,queries=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={e:i for i,e in enumerate(f['edge_ids'])};q=r['query'];assert q==p['query']==next(x for x in queries if x['connection_id']==q['connection_id']);assert len(pool['462'])==1 and len(pool['462'][0]['records'])==1 and q['net_id']==462;old=pool['462'][0]['records'][0];assert all(q[k]==old[k] for k in q);channels=sorted(n for n in pool['462'][0]['nodes'] if nodes[n].get('type') in ('CHANX','CHANY'));assert channels==r['original_channel_nodes']==p['original_channel_nodes'];owners=defaultdict(set)
for rec in seed:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
assert not owners[462];base=Counter(n for s in owners.values() for n in s);fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};budget=max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2);assert budget==r['budget']==p['budget'];cap=budget+1;assert all(x>=0 for x in rc.increments);ban_sets=[[]]+[[n] for n in channels]+([channels] if len(channels)>1 else []);contexts=['exact_seed','all_seed_occupancy_relaxed'];assert p['contexts']==contexts and p['ban_sets']==ban_sets;assert len(r['rows'])==2*len(ban_sets) and {(x['context'],x['probe']) for x in r['rows']}=={(c,i) for c in contexts for i in range(len(ban_sets))};checks=0;results=[]
for row in r['rows']:
 banned=set(ban_sets[row['probe']]);assert row['banned_nodes']==ban_sets[row['probe']];allowed=bytes((base[n]<f['capacities'][n] if row['context']=='exact_seed' else f['capacities'][n]>0) and n not in banned for n in range(len(nodes)));assert allowed==Path(row['allowed_file']).read_bytes();raw=Path(row['certificate_file']).read_bytes();assert len(raw)==8*len(nodes);d=struct.unpack('<'+str(len(nodes))+'Q',raw);assert all(x<=cap for x in d);assert d[q['source']]==(min(cap,rc.initial(q['source'])) if allowed[q['source']] else cap)
 for u in range(len(nodes)):
  if not allowed[u]:assert d[u]==cap;continue
  if d[u]==cap:checks+=f['row_offsets'][u+1]-f['row_offsets'][u];continue
  for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][edge]
   if allowed[v]:assert d[v]<=min(cap,d[u]+rc.increments[edge]);checks+=1
 reached={q['source']} if allowed[q['source']] and d[q['source']]<cap else set();queue=deque(reached)
 while queue:
  u=queue.popleft()
  for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][edge]
   if allowed[v] and v not in reached and d[v]<cap and d[v]==d[u]+rc.increments[edge]:reached.add(v);queue.append(v)
 assert reached=={n for n,x in enumerate(d) if x<cap};assert row['minimum_capped_delay']==d[q['sink']];feasible=d[q['sink']]<=budget;assert feasible==row['budget_feasible']
 if feasible:
  path=row['physical_edge_ids'];assert rc.path(q['source'],q['sink'],path)==d[q['sink']];u=q['source'];used={u}
  for eid in path:edge=slots[eid];assert f['row_offsets'][u]<=edge<f['row_offsets'][u+1];u=f['dest_ranks'][edge];assert allowed[u] and u not in used;used.add(u)
  assert u==q['sink'] and not used.intersection(banned)
 else:assert row['physical_edge_ids'] is None
 results.append(dict(context=row['context'],banned_nodes=row['banned_nodes'],budget_feasible=feasible));print('PASS channel probe',row['context'],row['banned_nodes'],feasible,flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=results,exact_certificates=len(r['rows']),all_arc_inequalities_including_tautologies=checks,all_original_channel_probes_scope_and_physical_witnesses_pass=True,scope='Original budget exactseed alternatives, plus unrestricted occupancy diagnosis. Seed-relaxed witnesses never legal candidate commits; negative certificate scope fixed graph/endpoint/budget/model, not native/globalQoR/workflow.'),indent=2)+'\n');print('PASS NET462 channel necessity',len(results),flush=True)
