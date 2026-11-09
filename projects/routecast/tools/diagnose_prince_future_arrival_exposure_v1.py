"""Retrospective search-exposure and phase-acquisition attribution, never a forecaster."""
import json,time
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from verify_prince_ownership_ledger_v2 import owner_payload
from evaluate_prince_ready_owner_forecast_v1 import final_owners
R=Path(__file__).resolve().parents[1];E=R/'experiments';L=E/'prince_ownership_ledger_trial_v2_2026-10-20';F=E/'prince_ready_owner_forecast_v1_2026-10-20';D=E/'prince_future_arrival_exposure_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def pairs(owners):return {(net,n) for net,ns in owners.items() for n in ns}
def main():
 D.mkdir(exist_ok=False);start=time.perf_counter();frozen=load(F/'frozen_inputs.json');proof=load(L/'ledger_verification_v1.json');prior=load(F/'verification.json');priorby={r['case']:r for r in prior['rows']};bindings={str(p):sha(p) for p in [F/'frozen_inputs.json',F/'verification.json',L/'ledger_verification_v1.json',Path(__file__)]};rows=[]
 (D/'protocol.json').write_text(json.dumps(dict(status='RETROSPECTIVE_DIAGNOSTIC_NOT_PREDICTOR',scope='All9 original cases. Join already frozen post-ready observed CHANNEL query pairs to same-phase ownership boundaries and unchanged-native final legal routes. Future acquisitions and queries are diagnostic labels,not ready-time features.',definitions=dict(global_arrival='final occupied resource unoccupied at ready',new_owner_pair='final NET/resource pair not owned by that NET at ready; includes transfers and formerly empty resources',immediate_exposure='NET/resource appeared in linker-observed CHANNEL cost queries during first post-ready iteration',first_acquisition='first saved end-of-iteration phase boundary afterready containing final NET/resource pair; not first intra-iteration add and not proof of continuous retention'),limitations=['Unobserved query pair does not prove never searched; inlined/call-local costs are not exhaustively instrumented.','Queries/acquisition after ready cannot be deployed as ready-time input.','Do not replace original prediction gates with diagnostic coverage.','No causal attribution to box expansion or NET relocation without additional geometric/event proof.']),indent=2)+'\n')
 bindings[str(D/'protocol.json')]=sha(D/'protocol.json')
 for entry in frozen['rows']:
  c=entry['case']
  if not entry['available']:rows.append(dict(case=c,status='NO_READY_OR_LEGAL_LABEL'));continue
  src=L/c/'capture';t=entry['ready_iteration'];op=src/'owners'/f'owners_{t}.bin';it,ready=owner_payload(op);assert it==t and sha(op)==proof['bindings'][str(op)];ready_pairs=pairs(ready);ready_nodes={n for net,n in ready_pairs};label=src/'output.route';final=final_owners(label);final_pairs=pairs(final);assert len(final_pairs)==len({n for net,n in final_pairs});original=E/'prince_native_cohort_v1_2026-10-20'/c/'output.route';assert final_pairs==pairs(final_owners(original));new=final_pairs-ready_pairs;global_new={n for net,n in new if n not in ready_nodes};transfer={n for net,n in new if n in ready_nodes};assert not global_new&transfer
  qp=Path(entry['input_path']);assert sha(qp)==entry['input_sha256'];observed=set();qnodes=set();calls=groups=0
  for net,node,ident,forecast,baseline,count in map(json.loads,qp.open()):observed.add((net,node));qnodes.add(node);calls+=count;groups+=1
  assert calls==entry['calls'] and groups==entry['groups'];connections=src/'queries.tsv.connections.tsv';active=set();connection_count=0
  for line in connections.open():
   i,ident,net,pin,sink,size=map(int,line.split())
   if i==t+1:active.add(net);connection_count+=1
  assert {net for net,node in observed}<=active;first={};next_pairs=None;phases=[]
  for p in sorted((src/'owners').glob('owners_*.bin'),key=lambda p:int(p.stem.split('_')[1])):
   i=int(p.stem.split('_')[1])
   if i<=t:continue
   ii,owners=owner_payload(p);assert i==ii;assert sha(p)==proof['bindings'][str(p)];current=pairs(owners);phases.append(i)
   if i==t+1:next_pairs=current
   for pair in new&current:first.setdefault(pair,i)
   bindings[str(p)]=sha(p)
  assert next_pairs is not None and phases==list(range(t+1,max(phases)+1));out=D/c;out.mkdir(parents=True);ap=out/'arrival_pairs.jsonl';stats=defaultdict(Counter);hist=Counter()
  with ap.open('x') as f:
   for net,node in sorted(new):
    category='empty_at_ready' if node in global_new else 'owner_transfer';acquired=first.get((net,node));r=dict(net=net,node=node,category=category,next_NET_active=net in active,next_same_pair_observed=(net,node) in observed,next_resource_observed=node in qnodes,held_at_next_boundary=(net,node) in next_pairs,first_saved_acquisition=acquired,terminal_only=acquired is None);f.write(json.dumps(r,separators=(',',':'))+'\n');s=stats[category];s['pairs']+=1
    for k in ['next_NET_active','next_same_pair_observed','next_resource_observed','held_at_next_boundary','terminal_only']:s[k]+=r[k]
    if acquired is not None:hist[acquired-t]+=1;s['first_acquired_next_boundary']+=acquired==t+1;s['first_acquired_later_boundary']+=acquired>t+1
  stats={k:dict(v) for k,v in stats.items()};rows.append(dict(case=c,status='EXPOSURE_AND_PHASE_ACQUISITION_ATTRIBUTED',ready_iteration=t,final_phase=max(phases),ready_occupied_resources=len(ready_nodes),final_occupied_resources=len(final_pairs),global_new_resources=len(global_new),new_final_owner_pairs=len(new),owner_transfer_resources=len(transfer),next_query_pairs=len(observed),next_query_nodes=len(qnodes),next_active_NETs=len(active),next_connection_calls=connection_count,groups=groups,cost_calls=calls,categories=stats,first_saved_acquisition_offset_histogram=dict(sorted(hist.items())),arrival_file=str(ap)))
  for p in [op,label,original,qp,connections,ap]:bindings[str(p)]=sha(p)
  print('FUTURE_ARRIVAL_EXPOSURE',c,len(global_new),stats,flush=True)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items())
 (D/'verification.json').write_text(json.dumps(dict(status='POST_READY_FUTURE_ARRIVAL_EXPOSURE_DIAGNOSED',rows=rows,bindings=bindings,seconds=time.perf_counter()-start,full9_gate=False,scope='Retrospective exposed-development diagnosis;not a prediction score,causal explanation,or native/fullpaid/unseen claim.'),indent=2)+'\n')
if __name__=='__main__':main()
