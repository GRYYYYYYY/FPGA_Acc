"""Compare the corrected control with exposed historical arms; no paired-time claim."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/mmc_trim_native_control_v2_2026-10-21'
T=D/'audit/verification.json';t=json.loads(T.read_text())
H=R/'experiments/mmc_native_seed_utility_pilot_v1_2026-10-18'
L=H/'local_terminal_audit_v1/verification.json';l=json.loads(L.read_text())
RP=H/'rows.json';raw=next(r for r in json.loads(RP.read_text()) if r['arm']=='raw')
for r in [t,l,raw]:
 assert r['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS'
 c=r['canonical'];assert c['semantic_consistency_gate_pass'] and c['packed_netlist_byte_identical'] and c['all_NET_physical_node_type_switch_sequences_identical']
 assert all(sha(p)==h for p,h in c['files'].items())
for r in [t,l]:assert all(sha(p)==h for p,h in r['bindings'].items())
keys=['iterations','wirelength','diagnostic_cpd_ns','native_process_seconds']
work=['total_heap_pushes','total_rerouted_NET_operations','total_rerouted_connection_operations','printed_routing_seconds']
summary={}
for name,r in [('trim_v2',t),('raw',raw),('local',l)]:
 summary[name]={k:r[k] for k in keys};summary[name].update({k:r['native_work'][k] for k in work});summary[name]['original_zero_counter_gate_pass']=r['canonical']['original_zero_counter_gate_pass']
delta={name:{k:summary[name][k]-summary['trim_v2'][k] for k in keys+work} for name in ['raw','local']}
out={'arms':summary,'minus_trim_v2':delta,'corrected_control_all_semantic_gates_pass':True,'original_failed_trim_still_failed':True,'scope':'Exposed same MMC target, prepared seeds; corrected control measured later, no randomization or repeated whole-workflow observations. Async CPD diagnostic. Original failed protocol not retroactively promoted.','decision':'Use this as a corrected control observation only. Native clock excludes graph/source capture, model/seed generation and full gate costs. Evaluate work and QoR deltas together; no claim of end-to-end or heldout/hardware acceleration.','bindings':{str(p):sha(p) for p in [Path(__file__),T,L,RP,D/'protocol.json',H/'terminal_recovery_decision_v1.json']}}
prep=R/'experiments/mmc_native_local_seed_v1_2026-10-18/receipt.json'
pr=json.loads(prep.read_text());assert all(sha(k)==v for k,v in pr['bindings'].items())
observed_native_saving=summary['trim_v2']['native_process_seconds']-summary['local']['native_process_seconds']
out['prepared_component_cost_screen']={'historical_local_seed_preparation_seconds':pr['preparation_seconds'],'observed_trim_v2_minus_local_native_seconds':observed_native_saving,'preparation_minus_observed_native_saving_seconds':pr['preparation_seconds']-observed_native_saving,'interpretation':'Historical component screen, not a paired end-to-end sum or global bound. Local seed preparation alone is larger than observed native saving before model/capture/gate charges. Do not spend six full observations on this unchanged file-oriented implementation as an acceleration candidate; first establish a charged state-lifetime API or other concrete avoidable-work mechanism.'}
out['bindings'][str(prep)]=sha(prep)
(D/'comparison_v2.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
