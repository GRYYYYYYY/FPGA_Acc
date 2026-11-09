"""Posthoc NET gain and closure accounting; no prediction/gate mutations."""
import array,json
from pathlib import Path
from collections import Counter,defaultdict,deque
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/mmc_owner_NET_gain_diagnosis_v1_2026-10-19';out.mkdir(exist_ok=False);cp=R/'experiments/mmc_resource_context_v1_2026-10-19/CHANNEL_ids.u32';ids=array.array('I');ids.frombytes(cp.read_bytes());channels=set(ids);master=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=read(master);bindings={str(p):sha(p) for p in [cp,master,Path(__file__).resolve()]};rows=[]
 for item in plan['cases']:
  case=item['case'];root=R/f'experiments/mmc_owner_frequency_development_v1_2026-10-19/{case}';choicep=root/'choices.jsonl';choices={x['net_id']:x for x in map(json.loads,choicep.open())};bp=R/f'experiments/mmc_candidate_ownership_implications_v1_2026-10-19/{case}/banks.jsonl';banks={x['net_id']:(set(x['A']),set(x['B'])) for x in map(json.loads,bp.open())};gp=bp.with_name('graph.json');g=read(gp);tp=Path(item['native_label']);assert sha(tp)==plan['bindings'][str(tp)];truth={int(n):v for n,v in read(tp)['node_occupancy'].items()};A=Counter(n for a,b in banks.values() for n in a);B=Counter(n for a,b in banks.values() for n in b);safe={n for n in channels if A[n]<=1 and B[n]<=1};assert all(truth.get(n,0) in (0,1) for n in safe);weights={net:sum(1-2*truth.get(n,0) for n in (a-b)&safe)-sum(1-2*truth.get(n,0) for n in (b-a)&safe) for net,(a,b) in banks.items()};selected={n for n,c in choices.items() if c['pick']=='B'}
  oraclep=R/f'experiments/mmc_aggregate_L1_oracle_v1_2026-10-19/{case}/choices.jsonl';oracle={x['net_id']:x for x in map(json.loads,oraclep.open())};assert set(oracle)==set(choices)==set(weights)
  for n,w in weights.items():assert oracle[n]['aggregate_gain']==w
  optimum={n for n,c in oracle.items() if c['pick']=='B'};adj=defaultdict(list)
  for e in g['edges']:adj[e['source']].append(e['target'])
  seeds={n for n in selected if choices[n]['expected_gain_scaled']>0};closure=set(seeds);queue=deque(seeds)
  while queue:
   n=queue.popleft()
   for v in adj[n]:
    if v not in closure:closure.add(v);queue.append(v)
  assert closure<=selected
  groups={}
  for name,ns in [('selected',selected),('selected_positive_predicted',seeds),('selected_nonpositive_predicted',selected-seeds),('nonpositive_required_by_selected_positive_seeds',closure-seeds),('selected_outside_positive_seed_closure',selected-closure),('oracle_only',optimum-selected),('model_only',selected-optimum),('shared',selected&optimum)]:
   groups[name]=dict(NETs=len(ns),positive_actual_NETs=sum(weights[n]>0 for n in ns),negative_actual_NETs=sum(weights[n]<0 for n in ns),true_gain=sum(weights[n] for n in ns),true_benefit=sum(max(0,weights[n]) for n in ns),true_harm=sum(max(0,-weights[n]) for n in ns),predicted_gain_scaled=sum(choices[n]['expected_gain_scaled'] for n in ns))
  ledger=Counter(n for net,(a,b) in banks.items() for n in (b if net in selected else a));assert all(ledger[n]<=1 for n in safe);before=sum(abs(A[n]-truth.get(n,0)) for n in safe);after=sum(abs(ledger[n]-truth.get(n,0)) for n in safe);actual=sum(weights[n] for n in selected);best=sum(weights[n] for n in optimum);assert before-after==actual and best-actual==groups['oracle_only']['true_gain']-groups['model_only']['true_gain'];assert best>=actual
  rows.append(dict(case=case,safe_CHANNELs=len(safe),safe_L1_before=before,safe_L1_after=after,actual_gain=actual,oracle_gain=best,regret=best-actual,groups=groups));bindings.update({str(p):sha(p) for p in [choicep,bp,gp,tp,oraclep]});print(case,'truegain',actual,'oracle',best,'regret',best-actual,'predicted',groups['selected']['predicted_gain_scaled']/1e6,'nonpositive',groups['selected_nonpositive_predicted']['NETs'],flush=True)
 with (out/'results.json').open('x') as f:json.dump(dict(status='ALL3_TRUE_NET_GAINS_DIRECT_SAFE_LOSS_REGRET_AND_SEED_CLOSURES_ACCOUNTED',rows=rows,bindings=bindings,scope='Target-using diagnostic only. NET true gains additive on protected safe domain for closed choices, not full-domain rank changes. Required closure is relative to retaining selected positive-predicted seeds, not an independent causal attribution or mandatory global optimum.'),f,indent=2)
if __name__=='__main__':main()
