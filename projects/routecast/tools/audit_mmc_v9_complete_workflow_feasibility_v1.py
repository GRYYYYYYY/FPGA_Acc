"""Authenticated stage arithmetic and limiting bounds; no claimed optimization or new timing."""
import hashlib,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 root=R/'experiments/ultraembedded_mmc_continuous_workflow_v9_2026-10-09'
 verification=root/'verification.json';stages=root/'stage_cost_verification_v6.json';handoff=root/'seed/handoff/mmc/receipt.json'
 v=json.loads(verification.read_text());s=json.loads(stages.read_text());h=json.loads(handoff.read_text());assert v['all_cases_both_complete_arms_authenticated'] and s['stage_accounting_pass']
 authenticated={}
 for x in [v,s]:
  for p,digest in x['bindings'].items():assert p not in authenticated or authenticated[p]==digest;authenticated[p]=digest
 assert all(sha(p)==digest for p,digest in authenticated.items())
 rows={x['arm']:x for x in s['rows']};costs={}
 for arm,row in rows.items():
  cost={Path(x['log']).name if 'log' in x else x['stage']:x['seconds'] for x in row['stages']};assert len(cost)==len(row['stages']);costs[arm]=cost
 cold=v['cold_continuous_cohort_seconds'];seed=v['seed_continuous_cohort_seconds'];assert math.isclose(rows['cold']['total_seconds'],cold) and math.isclose(rows['seed']['total_seconds'],seed)
 model=costs['seed']['mmc_model_native_seed.log'];audits=sum(costs['seed'][k] for k in ['mmc_initial_audit.log','mmc_sketch_audit.log','mmc_events_audit.log']);extra=model+audits
 native_cold=costs['cold']['native.log'];native_seed=costs['seed']['native.log'];excess=seed-cold
 assert h['selected_connections']+h['pending_connections']==h['required_connections']==115572
 residual=seed-extra;maximum_native_saving=native_seed;required_overhead_reduction_even_zero_native=max(0,excess-maximum_native_saving)
 sensitivity=[]
 for fraction in [0,.5,.9,1]:
  unchanged_native=seed-fraction*extra;zero_native=unchanged_native-native_seed
  sensitivity.append(dict(hypothetical_eliminated_seed_specific_fraction=fraction,seed_seconds_unchanged_native=unchanged_native,seed_seconds_zero_native=zero_native,break_even_unchanged_native=unchanged_native<cold,break_even_zero_native=zero_native<cold))
 report=dict(all_pass=True,measured=dict(cold_continuous_seconds=cold,seed_continuous_seconds=seed,seed_over_cold=seed/cold,native_cold_seconds=native_cold,native_seed_seconds=native_seed,seed_specific_model_handoff_seconds=model,three_full_audits_seconds=audits,combined_seed_specific_seconds=extra,full_excess_seconds=excess),hypothetical_bounds=dict(zero_three_audits_seed_seconds=seed-audits,zero_model_handoff_seed_seconds=seed-model,zero_all_seed_specific_seed_seconds=residual,remaining_gain_budget_if_all_seed_specific_zero=cold-residual,zero_native_alone_seed_seconds=seed-native_seed,minimum_seed_specific_fraction_to_remove_even_with_zero_native=required_overhead_reduction_even_zero_native/extra,maximum_remaining_seed_specific_cost_even_with_zero_native=extra-required_overhead_reduction_even_zero_native),sensitivity=sensitivity,seed_coverage=dict(required=h['required_connections'],selected=h['selected_connections'],pending=h['pending_connections'],selected_fraction=h['selected_connections']/h['required_connections']),decision='No new complete rerun of the same candidate is justified by isolated search acceleration alone. Need concrete changes in paid acquisition/model/auditing costs and demonstrated exact-router work reduction; retain all full validation and pending connections.',scope='One existing exposed MMC sequential cold-then-seed trial; authenticated producer stage arithmetic only, not independent clock reconstruction, paired replication, actual zero costs or measured optimization. Does not transfer neuron standalone model timings to MMC native workflow.',bindings={str(p):sha(p) for p in [Path(__file__).resolve(),verification,stages,handoff]},promoted=False)
 out=R/'experiments/mmc_v9_complete_workflow_feasibility_v1_2026-10-17';out.mkdir();(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['measured','hypothetical_bounds','seed_coverage']},indent=2))
if __name__=='__main__':main()
