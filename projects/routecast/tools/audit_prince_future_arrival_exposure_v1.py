"""Inverse-owner/terminal-ledger attribution audit and exposure denominators."""
import json,struct
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from verify_prince_ready_owner_forecast_v1 import ready_inverse,final_inverse
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_future_arrival_exposure_v1_2026-10-20';L=E/'prince_ownership_ledger_trial_v2_2026-10-20';F=E/'prince_ready_owner_forecast_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def main():
 v=load(D/'verification.json');assert all(sha(p)==h for p,h in v['bindings'].items());inputs={x['case']:x for x in load(F/'frozen_inputs.json')['rows']};rows=[];total=0;bindings={str(p):sha(p) for p in [D/'verification.json',Path(__file__),F/'independent_verification_v1.json']}
 for row in v['rows']:
  if row['status']!='EXPOSURE_AND_PHASE_ACQUISITION_ATTRIBUTED':continue
  c=row['case'];src=L/c/'capture';t=row['ready_iteration'];ready=ready_inverse(src/'owners'/f'owners_{t}.bin');lp=src/'queries.tsv.ledger.bin';terminal=final_inverse(lp);bindings[str(lp)]=sha(lp);assert all(len(ns)==1 for ns in terminal.values());new={(net,n) for n,ns in terminal.items() for net in ns if net not in ready.get(n,set())};records=list(map(json.loads,Path(row['arrival_file']).open()));assert {(x['net'],x['node']) for x in records}==new and len(records)==len(new)
  expected_first={};next_inv=None
  for i in range(t+1,row['final_phase']+1):
   inv=ready_inverse(src/'owners'/f'owners_{i}.bin')
   if i==t+1:next_inv=inv
   for net,n in new:
    if net in inv.get(n,set()):expected_first.setdefault((net,n),i)
  qp=Path(inputs[c]['input_path']);query={};calls=0
  for net,n,ident,forecast,baseline,count in map(json.loads,qp.open()):query.setdefault(n,set()).add(net);calls+=count
  assert calls==row['cost_calls'];active={int(line.split()[2]) for line in (src/'queries.tsv.connections.tsv').open() if int(line.split()[0])==t+1};raw=(src/'boundary'/f'iteration_{t}.bin').read_bytes();rr={n:(kind,occ,cap) for n,kind,occ,cap,acc in struct.iter_unpack('<QIiiI',raw[24:])};dirty=set()
  for n,ns in ready.items():
   kind,occ,cap=rr[n];assert kind in [4,5] and occ==len(ns)
   if occ>cap:dirty.update(ns)
  stats=defaultdict(Counter)
  for x in records:
   net,n=x['net'],x['node'];assert x['category']==('empty_at_ready' if not ready.get(n) else 'owner_transfer');assert x['next_NET_active']==(net in active);assert x['next_same_pair_observed']==(net in query.get(n,set()));assert x['next_resource_observed']==(n in query);assert x['held_at_next_boundary']==(net in next_inv.get(n,set()));assert x['first_saved_acquisition']==expected_first.get((net,n));assert x['terminal_only']==((net,n) not in expected_first);s=stats[x['category']];s['pairs']+=1
   for k in ['next_NET_active','next_same_pair_observed','next_resource_observed','held_at_next_boundary','terminal_only']:s[k]+=x[k]
   if not x['terminal_only']:s['first_acquired_next_boundary']+=x['first_saved_acquisition']==t+1;s['first_acquired_later_boundary']+=x['first_saved_acquisition']>t+1
   total+=1
  assert {k:dict(x) for k,x in stats.items()}==row['categories'];query_newpairs={(net,n) for n,ns in query.items() for net in ns if net not in ready.get(n,set())};query_empty_nodes={n for n in query if not ready.get(n)};global_arrivals={n for net,n in new if not ready.get(n)};tp=len(query_empty_nodes&global_arrivals);pairtp=len(query_newpairs&new);next_empty_pairs={(net,n) for n,ns in terminal.items() if not ready.get(n) for net in ns};dirtycovered=sum(net in dirty for net,n in next_empty_pairs)
  results=dict(case=c,arrival_records=len(records),ready_conflicted_NETs=len(dirty),future_global_arrivals_from_ready_conflicted_NETs=dirtycovered,future_global_arrivals=len(global_arrivals),any_NET_exposure=dict(predicted_empty_nodes=len(query_empty_nodes),true_arrivals=tp,false_positive=len(query_empty_nodes)-tp,precision=tp/len(query_empty_nodes),recall=tp/len(global_arrivals)),same_NET_exposure=dict(predicted_new_pairs=len(query_newpairs),true_new_final_pairs=pairtp,false_positive=len(query_newpairs)-pairtp,precision=pairtp/len(query_newpairs),recall=pairtp/len(new)))
  rows.append(results);print('EXPOSURE_AUDIT',c,results,flush=True)
 assert len(rows)==6
 out=dict(status='INVERSE_PHASE_AND_TERMINAL_LEDGER_ATTRIBUTION_RECONCILED',arrival_records=total,rows=rows,bindings=bindings,scope='Independent inverse phase owners and terminal event ledger; frozen query subset whose raw-query derivation/metrics was previously independently checked. Raw multi-million-row query files not rescanned here. Query exposure not a causal/predictive gate or proof of exhaustive search coverage. Conflict means ready owner touches overcapacity CHANNEL,not complete native reroute policy.')
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
if __name__=='__main__':main()
