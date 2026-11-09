"""Independent terminal ledger outcomes and fixed first-two-round response audit."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from verify_prince_ready_owner_forecast_v1 import ready_inverse,final_inverse
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_cost_advance_ablation_trial_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def pairs(inv):return {(net,n) for n,ns in inv.items() for net in ns}
def grouping(ps):
 d=defaultdict(set)
 for net,n in ps:d[net].add(n)
 return d
def main():
 source=D/'outcome_comparison_v1.json';v=load(source);native=load(D/'verification.json');by={r['case']:r for r in native['rows']};hp=E/'prince_cumulative_prefix_novelty_v1_2026-10-20/frozen_inputs.json';hist={r['case']:r for r in load(hp)['rows']};rows=[];response=[]
 for base in sorted({r['case'].rsplit('/',1)[0] for r in v['rows']}):
  ready=by[base+'/native']['ready_iteration'];ctrl=final_inverse(D/base/'native/queries.tsv.ledger.bin');gold=pairs(ctrl);goldgroup=grouping(gold);rp=pairs(ready_inverse(D/base/'native/owners'/f'owners_{ready}.bin')) if ready else set();observed=set()
  if ready:
   for x in map(json.loads,Path(hist[base]['path']).open()):
    if x['preheap_phase_mask']:observed.add((x['net'],x['node']))
  for row in [r for r in v['rows'] if r['case'].rsplit('/',1)[0]==base]:
   inv=final_inverse(D/row['case']/'queries.tsv.ledger.bin');fp=pairs(inv);groups=grouping(fp);assert len(fp)==row['terminal_owner_pairs'];assert len(fp^gold)==row['owner_pairs_changed_from_control'];assert sum(groups.get(n,set())!=goldgroup.get(n,set()) for n in groups.keys()|goldgroup.keys())==row['NETs_with_changed_terminal_CHANNELs'];assert len(inv.keys()^ctrl.keys())==row['global_occupied_resources_changed'];assert row['iterations']==by[row['case']]['iterations'] and row['native_exit_code']==by[row['case']]['native_exit_code']
   if ready:
    new=fp-rp;assert len(new)==row['new_terminal_owner_pairs'] and len(new-observed)==row['new_terminal_pairs_not_in_common_prefix'];assert (len(new-observed)/len(new) if new else None)==row['unobserved_common_prefix_fraction']
   else:assert row['status']=='UNACTIVATED_FAILURE_PRESERVED' and fp==gold
   rows.append(dict(case=row['case'],terminal_owner_pairs=len(fp)))
  if ready:
   phases={}
   for offset in [1,2]:
    i=ready+offset;sets={m:pairs(ready_inverse(D/base/m/'owners'/f'owners_{i}.bin')) for m in ['native','hold_pres','hold_acc','hold_both']}
    if offset==1:assert sets['native']==sets['hold_acc'] and sets['hold_pres']==sets['hold_both']
    phases[str(offset)]={m:len(p^sets['native']) for m,p in sets.items()}
   response.append(dict(case=base,phase_owner_pair_changes_vs_native=phases,first_post_native_hold_acc_equal=True,first_post_hold_pres_hold_both_equal=True))
  print('INDEPENDENT_COST_OUTCOME_PASS',base,flush=True)
 assert len(rows)==36 and len(response)==6
 with (D/'independent_outcome_verification_v1.json').open('x') as f:json.dump(dict(status='ALL36_TERMINAL_LEDGER_OUTCOMES_AND_FIXED_FIRST_TWO_ROUND_RESPONSE_RECONCILED',rows=rows,first_two_round_response=response,bindings={str(p):sha(p) for p in [source,D/'verification.json',hp,Path(__file__)]},scope='Terminal event ledgers versus primary printed-route sets. Exact ownership timing invariants,not raw-query byte equality (separate supplement). Failed routes retained as policy outcomes,never legal default prediction labels.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
