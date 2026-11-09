"""Offline all actual present-model fallback snapshots; not a new trajectory."""
import json,sys,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_structural_node_base_v1 import load as load_base
from load_initial_connection_criticalities_v1 import load as load_criticalities
from criticality_resident_joint_adapter_v2 import fallback
from criticality_shared_tree_sparse_reference_v2 import Graph
from criticality_ordered_net_primary_v1 import route as primary_route
from budget_NET_gate_reference_v1 import audit
from criticality_whole_net_choice_reference_v1 import score
O=R/'experiments/mmc_ordered_criticality_profile_v1_2026-10-10';O.mkdir();tick=time.perf_counter()
M=R/'experiments/mmc_present_guard_complete_v1_2026-10-10/model';P=M/'verification.json';proof=json.loads(P.read_text());assert proof['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass'];assert all(sha(p)==h for p,h in proof['bindings'].items())
bindings={**proof['bindings'],str(P):sha(P),**closure([Path(__file__)])}
r=json.loads((M/'receipt.json').read_text());endpoint=next(Path(p) for p in r['bindings'] if p.endswith('/endpoints.json'))
graph,digest,nodes,f,rc,queries=load_endpoints(endpoint);base,bb=load_base(len(f['capacities']),rc.scale);bindings.update(bb)
C=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10';criticalities=load_criticalities(C);cp=C/'verification.json';bindings.update(json.loads(cp.read_text())['bindings']);bindings[str(cp)]=sha(cp)
assert len(queries)==len(criticalities)==115572
for q in queries:
 c=criticalities[q['connection_id']];assert (q['net_id'],q['source'],q['sink'])==(c['net'],c['source_rr'],c['target_rr'])
slots={eid:i for i,eid in enumerate(f['edge_ids'])};groups=defaultdict(list);records=defaultdict(list)
for q in queries:groups[q['net_id']].append(q)
for x in json.loads((M/'initial.json').read_text())['records']:records[x['net_id']].append(x)
def own(recs):return {x['source'] for x in recs}|{f['dest_ranks'][slots[e]] for x in recs for e in x['answer']['physical_edge_ids']}
ledger=Counter(u for recs in records.values() for u in own(recs))
history=Counter({i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in {'CHANX','CHANY'}})
weight=rc.scale//(20*10**9);results=[]
workspace=Graph(f,rc.increments,[rc.initial(u) for u in range(len(f['capacities']))])
(O/'startup.json').write_text(json.dumps(dict(bindings=bindings,scope='All archived actual fallback snapshots, original trajectory and frozen initial criticality. No new feedback/QoR or future label tuning.'),indent=2)+'\n')
import cProfile,pstats
roundrow=r['rounds'][0];history.update({int(n):v for n,v in roundrow['changed_nodes'].items()})
# Replay earlier original commits to reconstruct the first actual fallback snapshot.
for event in roundrow['events']:
 net=event['net_id'];old=records[net];oldowned=own(old)
 if 'fallback' in event:break
 if event['status']=='COMMITTED':
  new=event['records'];newowned=own(new);ledger.subtract(oldowned-newowned);ledger.update(newowned-oldowned);records[net]=new
class Prices:
 def get(self,u,default=0):return base[u]+weight*history.get(u,0)+base[u]*max(0,ledger.get(u,0)-(u in oldowned)-f['capacities'][u]+1)
print('PROFILE START',net,len(groups[net]),flush=True)
prof=cProfile.Profile();begin=time.perf_counter();answer=prof.runcall(primary_route,workspace,groups[net],old,criticalities,Prices(),f['edge_ids']);elapsed=time.perf_counter()-begin
prof.dump_stats(str(O/'primary.prof'))
with (O/'profile.txt').open('w') as stream:pstats.Stats(prof,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(30)
for p in [O/'startup.json',O/'primary.prof',O/'profile.txt']:bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,net=net,pins=len(groups[net]),searched_pins=len(answer['search_results']),primary_complete=answer['complete'],profiled_seconds=elapsed,scope='cProfile of first actual fallback NET primary at exact original occupancy snapshot. Instrumentation overhead included. Not full MMC or speed evidence.'),indent=2)+'\n');print('PROFILE COMPLETE',elapsed,flush=True)
