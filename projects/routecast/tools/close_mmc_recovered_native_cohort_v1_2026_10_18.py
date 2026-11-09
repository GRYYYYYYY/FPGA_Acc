"""Compose accepted recovered arms, preserving failed/incomplete original history."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_recovered_native_cohort_v1_2026-10-18';O.mkdir(exist_ok=False);original=R/'experiments/mmc_native_seed_utility_pilot_v1_2026-10-18';pp=original/'protocol.json';protocol=json.loads(pp.read_text());assert all(sha(p)==h for p,h in protocol['bindings'].items());rows=json.loads((original/'rows.json').read_text());raw=next(x for x in rows if x['arm']=='raw');assert raw['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';assert next(x for x in rows if x['arm']=='trim')['exit_status']==1
lp=R/'experiments/mmc_native_postprocess_recovery_v1_2026-10-18/local_completed/verification.json';lv=json.loads(lp.read_text());assert lv['successful_native_output_reused_without_rerouting'] and all(sha(p)==h for p,h in lv['bindings'].items());local=lv['row'];tp=R/'experiments/mmc_native_trim_recovery_pilot_v2_2026-10-18/verification.json';tv=json.loads(tp.read_text());assert tv['single_native_physical_and_canonical_pass'] and all(sha(p)==h for p,h in tv['bindings'].items());trim=tv['rows'][0];assert trim['arm']=='trim'
summary={};bindings={str(p):sha(p) for p in [Path(__file__),pp,original/'rows.json',lp,tp]};bindings.update(lv['bindings']);bindings.update(tv['bindings'])
for name,row in [('trim',trim),('raw',raw),('local',local)]:
 assert row['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and row['exit_status']==0 and not row['native_timeout'];c=row['canonical'];assert c['semantic_consistency_gate_pass'] and c['all_NET_physical_node_type_switch_sequences_identical'] and c['packed_netlist_byte_identical'];assert all(sha(p)==h for p,h in c['files'].items());bindings.update(c['files']);summary[name]={k:row[k] for k in ['iterations','wirelength','diagnostic_cpd_ns','native_process_seconds','canonical_audit_seconds']};summary[name].update({k:v for k,v in row['native_work'].items() if k not in ['rows','iterations']});summary[name]['canonical']={k:c[k] for k in ['semantic_consistency_gate_pass','original_zero_counter_gate_pass','fixups','mismatches','native_ignored_only_mismatch_pins']}
# Original native process inputs and repaired trim command use identical routing options.
expected=protocol['commands']['raw'];assert protocol['commands']['local']==expected
recovery=R/'experiments/mmc_native_trim_recovery_pilot_v2_2026-10-18';assert json.loads((recovery/'protocol.json').read_text())['commands']['trim']==expected
for folder in [original/'raw',original/'local',recovery/'trim']:
 for name in ['design.net','design.place','design.blif']:
  assert sha(folder/name)==sha(original/'raw'/name);bindings[str(folder/name)]=sha(folder/name)
 for name in ['native.log','output.route','terminal.json']:bindings[str(folder/name)]=sha(folder/name)
comparisons={}
for control in ['trim','raw']:
 a=summary['local'];b=summary[control];comparisons['local_minus_'+control]={k:a[k]-b[k] for k in ['iterations','wirelength','diagnostic_cpd_ns','native_process_seconds','total_heap_pushes','total_rerouted_NET_operations','total_rerouted_connection_operations']}
assert all(sha(p)==h for p,h in bindings.items())
with (O/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,all_three_accepted_native_physical_canonical_semantic_results=True,original_v1_cohort_completed=False,original_trim_seed_import_failure_preserved=True,original_parent_interrupted_only_after_native_children_terminal=True,raw_and_local_successful_native_outputs_not_rerouted=True,repaired_trim_native_reexecuted=True,arms=summary,comparisons=comparisons,scope='Recovered native correctness/QoR evidence from raw original run, local original run+completed postchecks, corrected trim rerun. Not a new balanced-order complete timing cohort; all timings descriptive, no total-time or stable speedup proof. Cached floors retain inherited source-contract evidence and all-old minimum dual-certificate gap. No strict heldout, real STA or FPGA claim.'),f,indent=2);f.write('\n')
print(json.dumps(dict(arms=summary,comparisons=comparisons),indent=2),flush=True)
