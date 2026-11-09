"""Authenticate full candidate execution plus independent ignored-pin audit."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/ultraembedded_mmc_pin_index_native_v1_2026-10-08'
old=R/'experiments/ultraembedded_mmc_continuous_workflow_v2_2026-10-08/seed/canonical'
def load(p):return json.loads(p.read_text())
def auth(obj):
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k in ('bindings','files') and isinstance(v,dict):
    for p,h in v.items():assert sha(p)==h,p
   else:auth(v)
 elif isinstance(obj,list):
  for v in obj:auth(v)
paths=[D/'protocol.json',D/'receipt.json',D/'ignored_pin_verification_v1.json',old/'receipt.json',old/'ignored_pin_verification_v1.json',Path(__file__)]
p,r,ip,o,oi=[load(x) for x in paths[:-1]]
for obj in (p,r,ip,o,oi):auth(obj)
a=r['rows'][0]['canonical'];b=o['rows'][0]['canonical']
for key in ('semantic_consistency_gate_pass','packed_netlist_byte_identical','all_NET_physical_node_type_switch_sequences_identical','canonical_original_XML_arc_branch_capacity_pass'):assert a[key] and b[key]
for key in ('pins','cpd_ns','expected_cpd_ns','mismatches','fixups','native_ignored_only_mismatch_pins','original_zero_counter_gate_pass'):assert a[key]==b[key],key
assert a['pins']==115572 and a['exit_code']==0 and not a['original_zero_counter_gate_pass']
assert ip['rows']==oi['rows']
for key in ('every_mismatch_matches_native_ignored_sink_pin','post_reload_packed_netlist_byte_identical'):assert ip['rows'][0][key]
for name in ('design.route','design.net','design.net.post_routing'):assert (D/'mmc'/name).read_bytes()==(old/'mmc'/name).read_bytes()
bindings={str(x):sha(x) for x in paths}
result=dict(bindings=bindings,full_candidate_native_execution_and_independent_ignored_pin_audit_pass=True,all115572_sink_pins_and_complete_canonical_route_bytes_match=True,native_original_FULL_STA_XML_sequences_capacity_and_packed_bytes_pass=True,strict_zero_counter_gate_pass=False,candidate_elapsed_seconds=r['elapsed_seconds'],scope='One full MMC candidate semantic certification; elapsed includes graph/hash/native/audits within candidate call, excludes independent ignored audit. No paired timing, workflow gain, other-case generalization, original HDL or real async timing claim.')
assert all(sha(k)==v for k,v in bindings.items())
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('Full candidate and independent ignored gates PASS')
