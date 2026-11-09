"""Causal prefix exposure feasibility screen; no forecast trained/admitted."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from verify_prince_ready_owner_forecast_v1 import ready_inverse,final_inverse
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_causal_query_frontier_v1_2026-10-20';L=E/'prince_ownership_ledger_trial_v2_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def main():
 frozen=load(D/'frozen_inputs.json');assert all(sha(p)==h for p,h in frozen['bindings'].items());bindings={str(D/'frozen_inputs.json'):sha(D/'frozen_inputs.json'),str(Path(__file__)):sha(__file__)};rows=[]
 for row in frozen['rows']:
  c=row['case']
  if row['status']!='CAUSAL_QUERY_PAIRS_FROZEN':rows.append(dict(case=c,status=row['status']));continue
  src=L/c/'capture';t=row['ready_iteration'];op=src/'owners'/f'owners_{t}.bin';lp=src/'queries.tsv.ledger.bin';ready=ready_inverse(op);final=final_inverse(lp);new={(net,n) for n,ns in final.items() for net in ns if net not in ready.get(n,set())};newnodes={n for net,n in new if not ready.get(n)};obs={}
  for i,p in row['paths'].items():
   a=list(map(json.loads,Path(p).open()));assert len(a)==row['pairs_by_iteration'][i] and sum(x['calls'] for x in a)==row['calls_by_iteration'][i] and sum(x['state_groups'] for x in a)==row['state_groups_by_iteration'][i];obs[int(i)]={(x['net'],x['node']) for x in a};assert len(obs[int(i)])==len(a)
  results={}
  for name,observed in [('ready',obs[t]),('two_phase_union',obs[t]|obs[t-1])]:
   eligible={(net,n) for net,n in observed if net not in ready.get(n,set())};nodes={n for net,n in eligible if not ready.get(n)};tp=len(eligible&new);ntp=len(nodes&newnodes);results[name]=dict(new_pair_candidates=len(eligible),true_new_final_pairs=tp,new_pair_precision=tp/len(eligible),new_pair_recall=tp/len(new),global_arrival_candidates=len(nodes),true_global_arrivals=ntp,global_arrival_precision=ntp/len(nodes),global_arrival_recall=ntp/len(newnodes))
  rows.append(dict(case=c,status='CAUSAL_EXPOSURE_FEASIBILITY_SCREENED',new_final_owner_pairs=len(new),global_arrivals=len(newnodes),methods=results));print('CAUSAL_FRONTIER_SCREEN',c,results,flush=True)
  for p in [op,lp]:bindings[str(p)]=sha(p)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items())
 with (D/'feasibility_screen_v1.json').open('x') as f:json.dump(dict(status='CAUSAL_PREFIX_EXPOSURE_SCREEN_NOT_PREDICTOR',rows=rows,bindings=bindings,full9_gate=False,scope='Input pairs frozen before current label join,all exposed development. Candidate support/precision only;no score model,original metric gate,native/fullpaid/unseen promotion.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
