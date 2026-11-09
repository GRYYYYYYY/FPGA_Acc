"""Actual failure-state capacity-only shortest paths, own NET union charged once."""
import sys,json,time,heapq,struct
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_restored_owner_rollback_domains_v1_2026-10-07';out.mkdir();begin=time.perf_counter();parent=R/'experiments/misex_net466_budget_path_owner_joint_v3_2026-10-07';vp=parent/'branch_verification_dedup.json';v=json.loads(vp.read_text());assert v['states_verified']==8 and not v['local_solution_present'];rp=parent/'receipt.json';assert sha(rp)==v['bindings'][str(rp)];pr=json.loads(rp.read_text());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(vp):sha(vp),str(rp):sha(rp),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()})
for a in pr['attempts']:assert sha(a['state_file'])==v['bindings'][a['state_file']];bindings[a['state_file']]=sha(a['state_file'])
proposalparent=R/'experiments/misex_net466_budget_path_owner_release_v3_2026-10-07';
for asset in [proposalparent/'event.json',proposalparent/'core_options.json',proposalparent/'proposals.json',parent/'protocol.json']:bindings[str(asset)]=sha(asset);assert bindings[str(asset)]==v['bindings'][str(asset)]
event=json.loads((proposalparent/'event.json').read_text());options={int(n):ops for n,ops in json.loads((proposalparent/'core_options.json').read_text()).items()};proposals=json.loads((proposalparent/'proposals.json').read_text());protected=set(json.loads((parent/'protocol.json').read_text())['protected_original_connection_ids'])
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy='All8 frozen failure states; enumerate every OTHER NET with nonimmutable restored records. Rollback all its mutable records, keep ALL kept/core/protected initialseed and every other record unchanged. Compute failed-query ordinary RC budget feasibility with own NET union charge removed. Original budgets, capped certificates for every probe; witnesses are domain suggestions, no actual dropped-NET route commit.'),indent=2)+'\n');_,_,nodes,f,rc,queries=load_endpoints(ep);floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};slots={e:i for i,e in enumerate(f['edge_ids'])};rows=[]
for a in pr['attempts']:
 state=json.loads(Path(a['state_file']).read_text());q=state['failure']['query'];proposal=proposals[a['plan']['proposal_index']];seed=[x for x in event['before_records'] if x['net_id'] not in proposal['release'] or x['connection_id'] in protected]+[x for n,i in proposal['core_option_indices'].items() for x in options[int(n)][i]['records']];seedmap={x['connection_id']:x for x in seed};actual={x['connection_id']:x for x in state['records']};assert all(actual[cid]==rec for cid,rec in seedmap.items());mutable=defaultdict(list)
 for cid,rec in actual.items():
  if cid not in seedmap and rec['net_id']!=q['net_id']:mutable[rec['net_id']].append(cid)
 budget=max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2);cap=budget+1;checks=[]
 for net,cids in sorted(mutable.items()):
  kept=[x for cid,x in actual.items() if cid not in cids];owners=defaultdict(set)
  for rec in kept:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
  ledger=Counter(n for own in owners.values() for n in own);allowed=bytes(ledger[n]-int(n in owners[q['net_id']])<f['capacities'][n] for n in range(len(nodes)));d=[cap]*len(nodes);parents={};d[q['source']]=min(cap,rc.initial(q['source'])) if allowed[q['source']] else cap;queue=[(d[q['source']],q['source'])] if d[q['source']]<cap else []
  while queue:
   delay,u=heapq.heappop(queue)
   if d[u]!=delay:continue
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][slot]
    if not allowed[v]:continue
    cost=min(cap,delay+rc.increments[slot])
    if cost<d[v]:d[v]=cost;parents[v]=(u,slot);heapq.heappush(queue,(cost,v))
  folder=out/f"branch{a['index']}_rollback{net}";folder.mkdir();(folder/'allowed.bin').write_bytes(allowed);file=folder/'distances.bin';file.write_bytes(struct.pack('<'+str(len(nodes))+'Q',*d));path=None
  if d[q['sink']]<=budget:
   u=q['sink'];path=[];seen={u}
   while u!=q['source']:
    p,slot=parents[u];assert p not in seen;seen.add(p);path.append(f['edge_ids'][slot]);u=p
   path.reverse();assert rc.path(q['source'],q['sink'],path)==d[q['sink']]
  checks.append(dict(rollback_net=net,removed_connection_ids=sorted(cids),minimum_capped_delay=d[q['sink']],budget_feasible=path is not None,physical_edge_ids=path,certificate_file=str(file),allowed_file=str(folder/'allowed.bin')))
 feasible=sorted((x for x in checks if x['budget_feasible']),key=lambda x:(len(x['removed_connection_ids']),x['minimum_capped_delay'],x['rollback_net']));rows.append(dict(branch=a['index'],state_file=a['state_file'],query=q,budget=budget,checks=checks,ranked_feasible_rollback_nets=[x['rollback_net'] for x in feasible]));print('ROLLBACK DOMAINS',a['index'],len(checks),[(x['rollback_net'],len(x['removed_connection_ids'])) for x in feasible],flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
