"""Close all fixed native pilot arms; no full workflow timing inference."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_native_seed_utility_pilot_v1_2026-10-18';p=D/'verification.json';v=json.loads(p.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());assert [r['arm'] for r in v['rows']]==['trim','raw','local'];summary={}
for row in v['rows']:
 summary[row['arm']]={k:row.get(k) for k in ['status','exit_status','native_timeout','iterations','wirelength','diagnostic_cpd_ns','native_process_seconds','canonical_audit_seconds','error']}
 if row['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS':
  c=row['canonical'];assert c['semantic_consistency_gate_pass'] and c['all_NET_physical_node_type_switch_sequences_identical'] and c['packed_netlist_byte_identical'];summary[row['arm']].update({k:x for k,x in row['native_work'].items() if k!='rows'});summary[row['arm']]['canonical']={k:c[k] for k in ['semantic_consistency_gate_pass','original_zero_counter_gate_pass','fixups','mismatches','native_ignored_only_mismatch_pins']}
comparisons={}
if v['all_three_native_physical_and_canonical_pass']:
 for baseline in ['trim','raw']:
  a=summary['local'];b=summary[baseline];comparisons['local_minus_'+baseline]={k:a[k]-b[k] for k in ['iterations','wirelength','diagnostic_cpd_ns','native_process_seconds','total_heap_pushes','total_rerouted_NET_operations','total_rerouted_connection_operations']}
fields=dict(bindings={str(p):sha(p),str(Path(__file__)):sha(__file__)},all_three_final_gates_pass=v['all_three_native_physical_and_canonical_pass'],arms=summary,comparisons=comparisons,decision='Report all work/iteration/wire/CPD tradeoffs and any failures. No promotion from component timing. Prepared cached-floor pilot does not replace six fresh whole-update timing observations.',limits='Same exposed MMC move/seed1 and fixed order; asynchronous CPD diagnostic, original zero-counter gate separately reported. Repeated NET/connection operations are not distinct seed survival counts. Old floors source-contract inherited, no fresh all-old independent minimum dual certificate. No total-time, heldout-family or hardware gain proof.')
with (D/'research_decision_v1.json').open('x') as f:json.dump(fields,f,indent=2);f.write('\n')
print(json.dumps(dict(arms=summary,comparisons=comparisons),indent=2),flush=True)
