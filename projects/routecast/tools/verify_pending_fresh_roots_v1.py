"""Independent allowed-mask, all-arc lower bound and realizing path proof."""
import sys,json,struct
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_fresh_root_diagnosis_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp),str(out/'protocol.json'):sha(out/'protocol.json')};assert all(sha(k)==h for k,h in bindings.items());parent=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07';bp=parent/'misex3/batch14.json';event=json.loads(bp.read_text());graph,digest,nodes,f,rc,queries=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');floor={(v['source'],v['sink']):v['minimum_integer'] for v in json.loads((parent/'misex3/floors.json').read_text())};slots={e:s for s,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in event['before_records']:
 assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
releases=[event['initial_release_net_ids']]+event['owner_swap']['screening']['proposed'];expected={(i,q['connection_id']) for i in range(len(releases)) for q in event['selection']['queries']};assert len(r['rows'])==len(expected)==16;seen=set();INF=(1<<64)-1;arc_checks=0
for row in r['rows']:
 index=row['release_index'];query=row['query'];key=(index,query['connection_id']);assert key in expected and key not in seen;seen.add(key);assert row['release']==releases[index] and query in event['selection']['queries'];counts=Counter(node for net,own in owners.items() if net not in row['release'] and net!=query['net_id'] for node in own);mask=bytes(f['capacities'][i]>counts[i] for i in range(len(nodes)));af=Path(row['allowed_file']);df=Path(row['distance_file']);assert sha(af)==row['allowed_sha256'] and sha(df)==row['distance_sha256'];bindings[str(af)]=sha(af);bindings[str(df)]=sha(df);assert af.read_bytes()==mask;data=df.read_bytes();assert len(data)==8*len(nodes);d=struct.unpack('<'+str(len(nodes))+'Q',data);src,sink=query['source'],query['sink'];assert d[sink]==0 if mask[sink] else all(v==INF for v in d);checks=0
 for u in range(len(nodes)):
  if not mask[u]:assert d[u]==INF;continue
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][s]
   if mask[v] and d[v]!=INF:assert d[u]!=INF and d[u]<=rc.increments[s]+d[v];checks+=1
 assert checks==row['full_allowed_arc_inequalities'];arc_checks+=checks;minimum=None if not mask[src] or d[src]==INF else rc.initial(src)+d[src];assert minimum==row['minimum_integer'];budget=max(rc.scale//10**9,(3*floor[(src,sink)]+1)//2);assert budget==row['budget'] and row['ordinary_budget_feasible']==(minimum is not None and minimum<=budget)
 if minimum is not None:
  assert rc.path(src,sink,row['physical_edge_ids'])==minimum;assert mask[src] and all(mask[f['dest_ranks'][slots[e]]] for e in row['physical_edge_ids'])
 else:assert not row['physical_edge_ids']
assert seen==expected and all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(all16_masks_minima_and_paths_verified=True,all_allowed_arc_checks=arc_checks,root_rejection_counts={str(i):sum(not row['ordinary_budget_feasible'] for row in r['rows'] if row['release_index']==i) for i in range(4)},bindings=bindings),indent=2)+'\n');print('PASS16 fresh-root exact minima/masks/paths',arc_checks,flush=True)
