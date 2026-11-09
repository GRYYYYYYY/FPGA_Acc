"""Exact-input current cold/seed QoR and explicitly different clock scopes."""
from pathlib import Path
from decimal import Decimal
import json,re
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10';C=R/'experiments/mmc_manifest_scope_cold_comparator_v1_2026-10-10';bindings={str(Path(__file__).resolve()):sha(Path(__file__)),str(R/'tools/pre_route_endpoints.py'):sha(R/'tools/pre_route_endpoints.py')}
def load(p):
 v=json.loads(p.read_text());bindings[str(p)]=sha(p);return v
sp=load(S/'verification.json');cp=load(C/'postchecks/verification.json')
assert sp['complete_current_MMC_initial_floors_paths_epochs_prices_ledgers_events_and_seed_native_pass'] and cp['all115572_native_physical_queries_and_full_XML_capacity_pass'] and cp['native_FULL_and_canonical_semantic_pass'] and cp['explicit_ignored_pin_audit_pass']
for v in [sp,cp]:assert all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings'])
a=load(S/'native/service_receipt.json');b=load(C/'native/receipt.json');assert a['command']==b['command'] and a['exit_code']==b['exit_code']==0 and a['seed_imported'] and not b['seed_imported']
for v in [a,b]:
 for sec in ['bindings','files']:assert all(sha(p)==h for p,h in v[sec].items());bindings.update(v[sec])
for name in ['design.blif','design.net','design.place']:assert sha(S/'native'/name)==sha(C/'native'/name)
assert sp['diagnostic_cpd_ns']==cp['diagnostic_cpd_ns']==15.7422 and sp['wirelength']==656069 and cp['wirelength']==661370
cold=Decimal(str(b['native_process_seconds']));audit=Decimal(str(load(S/'model/shared_audit_receipt.json')['local_seconds']));handoff=Decimal(str(sp['local_handoff_pipeline_seconds']));assert handoff>cold and audit>cold
result=dict(bindings=bindings,exact_current_binary_arch_RR_net_place_and_options_equal=True,both_complete_native_physical_canonical_ignored_audits_pass=True,printed_native_qor_nonregression_single_input=True,cold_wirelength=cp['wirelength'],seed_wirelength=sp['wirelength'],wirelength_relative_change=str(Decimal(sp['wirelength']-cp['wirelength'])/Decimal(cp['wirelength'])),printed_CPD_ns=sp['diagnostic_cpd_ns'],cold_iterations=int(re.search(r'Successfully routed after (\d+) routing iterations',(C/'native/native.log').read_text())[1]),seed_iterations=int(re.search(r'Successfully routed after (\d+) routing iterations',(S/'native/native.log').read_text())[1]),cold_native_subprocess_seconds=str(cold),seed_local_model_audit_handoff_native_seconds=str(handoff),seed_model_audits_local_seconds=str(audit),fixed_observed_model_audit_alone_exceeds_cold_native_subprocess=True,model_audit_excess_over_cold_subprocess_seconds=str(audit-cold),full_workflow_time_gain_proven=False,scope='One sequential exact-input-matched current cold run vs earlier current seed run, exposed MMC. Cold subprocess includes startup/RR loading; seed resume does not and is not divided into a speedup ratio. Seed local handoff includes model-specific full audits/native, excludes RR acquisition and final native/canonical audits. Neither full end-to-end common clocks nor repeated order-balanced timing available. Printed experimental CPD only, no real STA/functional/heldout/hardware claim. Fixed audit arithmetic is conditional diagnostic, not permission to remove validation.')
assert all(sha(p)==h for p,h in bindings.items());(C/'matched_seed_comparison.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['bindings','scope']})
