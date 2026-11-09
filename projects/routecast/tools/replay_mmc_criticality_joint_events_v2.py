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
from budget_NET_gate_reference_v1 import audit
from criticality_whole_net_choice_reference_v1 import score
O=R/'experiments/mmc_criticality_joint_event_replay_v2_2026-10-10';O.mkdir();tick=time.perf_counter()
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
(O/'startup.json').write_text(json.dumps(dict(bindings=bindings,scope='All archived actual fallback snapshots, original trajectory and frozen initial criticality. No new feedback/QoR or future label tuning.'),indent=2)+'\n')
for roundrow in r['rounds']:
 history.update({int(n):v for n,v in roundrow['changed_nodes'].items()})
 for event in roundrow['events']:
  net=event['net_id'];old=records[net];oldowned=own(old)
  if 'fallback' in event:
   parents={};settled=set();qs=groups[net]
   for a in event['primary_attempts']:
    if a['physical_edge_ids'] is None:continue
    q=next(q for q in qs if q['connection_id']==a['connection_id']);u=q['source']
    for e in a['physical_edge_ids']:
     slot=slots[e];v=f['dest_ranks'][slot];assert v not in parents or parents[v]==(u,slot);parents[v]=(u,slot);u=v
    assert u==q['sink'];settled.add(u)
   class Prices:
    def get(self,u,default=0):return weight*history.get(u,0)+base[u]*max(0,ledger.get(u,0)-(u in oldowned)-f['capacities'][u]+1)
   result=fallback(f,rc,slots,qs,old,parents,settled,Prices(),1,base,criticalities,10000)
   assert result['chosen_score']<=result['old_score']
   # independent traversal: per-pin delays and node user criticalities.
   from fractions import Fraction
   users={};rawcost=Fraction(0);jointparents={}
   for rec in result['records']:
    cid=rec['connection_id'];c=criticalities[cid];crit=Fraction(c['criticality_numerator'],c['criticality_denominator']);u=rec['source'];raw=rc.initial(u);seen={u}
    for eid in rec['answer']['physical_edge_ids']:
     slot=slots[eid];assert f['row_offsets'][u]<=slot<f['row_offsets'][u+1];v=f['dest_ranks'][slot];assert v not in seen;seen.add(v)
     assert v not in jointparents or jointparents[v]==(u,eid);jointparents[v]=(u,eid);users.setdefault(v,[]).append(crit);raw+=rc.increment(slot);u=v
    assert u==rec['sink'] and raw==rec['answer']['delay']<=rec['budget_integer'];rawcost+=crit*raw
   independent=rawcost+sum(((1-max(cs))*(base[u]+Prices().get(u)) for u,cs in users.items()),Fraction(0));assert independent==result['chosen_score']
   results.append(dict(round=roundrow['round_index'],net=net,status=result['status'],legacy_status=result['legacy_status'],states=result['states'],legacy_states=result['legacy_states'],search_status=result['search_status'],old_score=str(result['old_score']),chosen_score=str(result['chosen_score'])))
   if len(results)%100==0:print('REPLAY',len(results),flush=True)
  if event['status']=='COMMITTED':
   new=event['records'];newowned=own(new);ledger.subtract(oldowned-newowned);ledger.update(newowned-oldowned);records[net]=new
 assert sum(max(0,c-f['capacities'][n]) for n,c in ledger.items())==roundrow['overflow_after']
assert len(results)==1124
(O/'events.json').write_text(json.dumps(results)+'\n');bindings[str(O/'events.json')]=sha(O/'events.json');bindings[str(O/'startup.json')]=sha(O/'startup.json');assert all(sha(p)==h for p,h in bindings.items())
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,events=len(results),accepted=sum(x['status']=='ACCEPT_STRICT_IMPROVEMENT' for x in results),legacy_status_disagreements=sum(x['status']!=x['legacy_status'] for x in results),independent_chosen_score_raw_budgets_singleparent_pass=True,seconds=time.perf_counter()-tick,scope='Offline real snapshots only; no new candidate trajectory, overflow guard admission, native QoR, full independent XML reparse, or end-to-end speed evidence.'),indent=2)+'\n');print('MMC CRITICALITY EVENT REPLAY PASS',len(results),flush=True)
