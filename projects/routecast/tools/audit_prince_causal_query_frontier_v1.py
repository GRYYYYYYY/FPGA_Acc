"""Independent raw-column prefix extraction and printed-route support verification."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from evaluate_prince_ready_owner_forecast_v1 import final_owners
from verify_prince_ownership_ledger_v2 import owner_payload
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_causal_query_frontier_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def main():
 frozen=load(D/'frozen_inputs.json');screen=load(D/'feasibility_screen_v1.json');expected={r['case']:r for r in screen['rows']};checked=0;rows=[]
 for row in frozen['rows']:
  if row['status']!='CAUSAL_QUERY_PAIRS_FROZEN':continue
  c=row['case'];t=row['ready_iteration'];rawp=E/'prince_connection_query_trial_v1_2026-10-20'/c/'capture/queries.tsv';counts={t-1:defaultdict(lambda:[0,0,0,0]),t:defaultdict(lambda:[0,0,0,0])}
  for line in rawp.open():
   fields=line.rstrip().split('\t');i=int(fields[0])
   if i not in counts or fields[3] not in ['4','5']:continue
   net=int(fields[1])-1;node=int(fields[2]);occ=int(fields[4]);own=int(fields[15]);n=int(fields[16]);a=counts[i][net,node];a[0]+=n;a[1]+=1;a[2]+=n*own;a[3]+=n*int(occ-own>0)
  observed={}
  for i,groups in counts.items():
   actual={(x['net'],x['node']):[x['calls'],x['state_groups'],x['owned_calls'],x['live_other_positive_calls']] for x in map(json.loads,Path(row['paths'][str(i)]).open())};assert actual==dict(groups);observed[i]=set(actual);checked+=len(actual)
  src=E/'prince_ownership_ledger_trial_v2_2026-10-20'/c/'capture';it,ready=owner_payload(src/'owners'/f'owners_{t}.bin');gold=final_owners(src/'output.route');assert it==t;rp={(net,n) for net,ns in ready.items() for n in ns};fp={(net,n) for net,ns in gold.items() for n in ns};arrivals=fp-rp;rn={n for net,n in rp};an={n for net,n in arrivals if n not in rn};ex=expected[c];assert ex['new_final_owner_pairs']==len(arrivals) and ex['global_arrivals']==len(an)
  for name,support in [('ready',observed[t]),('two_phase_union',observed[t]|observed[t-1])]:
   candidates=support-rp;nodes={n for net,n in candidates if n not in rn};m=ex['methods'][name];assert m['new_pair_candidates']==len(candidates) and m['true_new_final_pairs']==len(candidates&arrivals) and m['global_arrival_candidates']==len(nodes) and m['true_global_arrivals']==len(nodes&an);assert m['new_pair_precision']==len(candidates&arrivals)/len(candidates) and m['new_pair_recall']==len(candidates&arrivals)/len(arrivals);assert m['global_arrival_precision']==len(nodes&an)/len(nodes) and m['global_arrival_recall']==len(nodes&an)/len(an)
  rows.append(dict(case=c,phase_pairs=sum(len(x) for x in observed.values())));print('CAUSAL_RAW_PREFIX_AND_PRINTED_LABEL_PASS',c,flush=True)
 assert len(rows)==6
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='RAW_PREFIX_COUNTERS_AND_PRINTED_ROUTE_TARGETS_RECONCILED',phase_pairs=checked,rows=rows,bindings={str(p):sha(p) for p in [D/'frozen_inputs.json',D/'feasibility_screen_v1.json',Path(__file__)]},scope='Raw files re-read using selected columns;all12 phase pair-count/call/ownership/other-demand arrays exact. Printed route labels independently reconcile binary-ledger screen. No score or original quality admission.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
