"""Report all observed native outcomes, no post-hoc acceptance threshold."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_proxy_budget_native_comparison_v1_2026-10-17'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
p=D/'verification.json';v=json.loads(p.read_text());assert v['all_three_native_physical_and_canonical_pass']
assert all(sha(k)==h for k,h in v['bindings'].items())
rows={r['arm']:r for r in v['rows']};assert set(rows)=={'cold','control','proxy'}
summary={};bindings={str(p):sha(p),str(Path(__file__).resolve()):sha(__file__)}
for arm,r in rows.items():
 assert not r['native_timeout'] and r['exit_status']==0 and r['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS'
 c=r['canonical'];assert c['semantic_consistency_gate_pass'] and c['all_NET_physical_node_type_switch_sequences_identical'] and c['packed_netlist_byte_identical']
 assert not c['original_zero_counter_gate_pass'] and c['native_ignored_only_mismatch_pins']==c['mismatches']==c['fixups']==26
 summary[arm]={k:r[k] for k in ['iterations','wirelength','diagnostic_cpd_ns','native_process_seconds','canonical_audit_seconds']}
 summary[arm].update({k:x for k,x in r['native_work'].items() if k not in ['rows','iterations']})
comparisons={}
for comparator in ['cold','control']:
 a=summary[comparator];b=summary['proxy'];keys=['iterations','wirelength','diagnostic_cpd_ns','native_process_seconds','total_heap_pushes','total_rerouted_NET_operations','total_rerouted_connection_operations','printed_routing_seconds']
 comparisons['proxy_minus_'+comparator]={k:dict(delta=b[k]-a[k],fractional_change=(b[k]-a[k])/a[k] if a[k] else None) for k in keys}
model_costs={}
for arm,folder in [('control','xtea_continue_primary_audit_fixture_v1_2026-10-17'),('proxy','xtea_proxy_budget_audit_fixture_v1_2026-10-17')]:
 model_costs[arm]={}
 for stage in ['model','initial_audit','sketch_audit','event_audit']:
  q=R/'experiments'/folder/(stage+'_terminal.json');d=json.loads(q.read_text());assert d['exit_status']==0;bindings[str(q)]=sha(q);model_costs[arm][stage]=d['seconds']
out=dict(bindings=bindings,all3_complete_native_physical_and_canonical_semantic_gates_pass=True,all3_original_zero_counter_gates_pass=False,ignored_pin_fixups_each_arm=26,arms=summary,proxy_comparisons=comparisons,archived_component_cost_seconds=model_costs,decision='Current exposed XTEA proxy seed reduces native operation counts and wirelength versus both controls, while taking17iterations versus cold16. Retain mixed-quality development candidate; no default promotion.',registration_accounting='An attempted additional prospective joint utility threshold was refused because output routes already existed. No such threshold was registered or used. This closure reports all outcomes descriptively, with no post-hoc pass threshold.',limits='One fixed-order observation per arm, same frozen settings, archived models reused. Repeated NET/connection operations are not distinct retained seed survival counts. Historical model/audit clocks are separate observations, not additive fresh complete workflow timing. CPD is diagnostic on experimental architecture. Original zero-counter canonical gate remains false; ignored-only semantic gate passed. No unseen family, stable native timing gain, end-to-end gain or hardware result.')
with (D/'research_decision_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(arms=summary,comparisons=comparisons),indent=2))
