"""Full manifest immutable round1 snapshot paired primary diagnostic; no feedback commits."""
import json,sys,time
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_structural_node_base_v1 import load as load_base
from load_initial_connection_criticalities_v1 import load as load_crit
from criticality_shared_tree_sparse_reference_v3 import Graph
from shared_frozen_present_snapshot_v1 import Snapshot
O=R/'experiments/mmc_native_snapshot_present_pair_v1_2026-10-10';O.mkdir()
N=R/'experiments/mmc_native_iteration_state_observer_v2_2026-10-10';T=R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10'
bindings=closure([Path(__file__)]);proofs=[N/'common_state_projection_verification_v1.json',N/'pin_identity_audit_v1.json',T/'independent_audits_verification.json',R/'experiments/scaled_frozen_present_contract_v1_2026-10-10/verification.json',R/'experiments/shared_frozen_present_snapshot_contract_v1_2026-10-10/verification.json']
for p in proofs:
 d=json.loads(p.read_text());assert all(sha(n)==h for n,h in d['bindings'].items());bindings.update(d['bindings']);bindings[str(p)]=sha(p)
endpoint=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';bindings[str(endpoint)]=sha(endpoint)
graph,digest,nodes,fields,rc,queries=load_endpoints(endpoint);assert len(queries)==115572
bases,b=load_base(len(nodes),rc.scale);bindings.update(b)
C=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10';criticalities=load_crit(C);cproof=C/'verification.json';bindings.update(json.loads(cproof.read_text())['bindings']);bindings[str(cproof)]=sha(cproof)
records={r['connection_id']:r for r in json.loads((T/'model/initial.json').read_text())['records']};assert len(records)==len(queries)
acc=[0]*len(nodes);occ=[0]*len(nodes);caps=[0]*len(nodes);owned=defaultdict(set);state=N/'states/round_1.tsv'
with state.open() as s:
 for line in s:
  f=line.split()
  if f[0]=='N':
   n=int(f[1]);occ[n]=int(f[2]);caps[n]=int(f[3]);value=Fraction(f[4]);assert value.denominator==1;acc[n]=int(value)
  elif f[0]=='T':owned[int(f[1])].add(int(f[2]))
assert all(a>=1 for a in acc) and caps==list(fields['capacities'])
groups=defaultdict(list)
for q in queries:
 r=records[q['connection_id']];assert all(r[k]==v for k,v in q.items());groups[q['net_id']].append(q)
assert len(groups)==55300
modes=[('unit',Fraction(1)),('observed_round2',Fraction(1,2))];snapshots={name:Snapshot(bases,acc,occ,caps,pf) for name,pf in modes};graphs={name:Graph(fields,[x*pf.denominator for x in rc.increments],[rc.initial(u)*pf.denominator for u in range(len(nodes))]) for name,pf in modes}
protocol={'bindings':bindings,'connections':115572,'nets':55300,'state_round':1,'present_modes':{name:str(pf) for name,pf in modes},'criticalities':'frozen initialized','budget_policy':'original budgets retained, denominator scaling exact','scope':'All manifest primary search diagnostic, per-pin budget tree acceptance only. Continues after budget failure explicitly; no wholeNET fallback, atomic commit, overflow gate, native route/QoR or netgain claim.'}
(O/'startup.json').write_text(json.dumps(protocol,indent=2)+'\n');counts={name:Counter() for name,pf in modes};tick=time.perf_counter()
with (O/'events.jsonl').open('w') as output:
 for number,(net,qs) in enumerate(sorted(groups.items()),1):
  order=sorted(qs,key=lambda q:(-Fraction(criticalities[q['connection_id']]['criticality_numerator'],criticalities[q['connection_id']]['criticality_denominator']),criticalities[q['connection_id']]['local_sink_pin'],q['connection_id']))
  event={'net_id':net,'order':[q['connection_id'] for q in order],'modes':{}}
  for name,pf in modes:
   view=snapshots[name].for_owner(owned[net]);tree=graphs[name].tree(order[0]['source']);results=[]
   for q in order:
    cid=q['connection_id'];c=criticalities[cid];value=Fraction(c['criticality_numerator'],c['criticality_denominator']);result=tree.expand(q['sink'],value,view,view.scale_raw(records[cid]['budget_integer']));slots=result.pop('path_slots',None)
    if slots is not None:
     path=[fields['edge_ids'][slot] for slot in slots];raw=rc.path(q['source'],q['sink'],path);assert result['raw']==raw*view.denominator;result['physical_edge_ids']=path;result['raw_unscaled']=raw
    results.append({'connection_id':cid,**result});counts[name][result['status']]+=1
   event['modes'][name]=results
  output.write(json.dumps(event)+'\n')
  if number%100==0:output.flush();print('PRESENT PAIR',number,sum(counts['unit'].values()),flush=True)
assert all(sum(c.values())==115572 for c in counts.values());assert all(sha(p)==h for p,h in bindings.items())
(O/'receipt.json').write_text(json.dumps({'bindings':bindings,'counts':{k:dict(v) for k,v in counts.items()},'events_sha256':sha(O/'events.jsonl'),'seconds':time.perf_counter()-tick,'independent_new_path_audits_complete':False,'scope':protocol['scope']},indent=2)+'\n');print('PRESENT PAIR COMPLETE',flush=True)
