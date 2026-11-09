"""Reconcile a recovered local audit, preserving original partial rows and failures."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
from audit_mmc_v16_native_iteration_work_v1 import parse
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_native_seed_utility_pilot_v1_2026-10-18'
p=D/'local_terminal_audit_v1/verification.json';local=json.loads(p.read_text())
assert local['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS'
assert all(sha(k)==v for k,v in local['bindings'].items())
rows=json.loads((D/'rows.json').read_text());assert [r['arm'] for r in rows]==['trim','raw']
raw=rows[1];assert raw['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS'
for r in [raw,local]:
 c=r['canonical'];assert c['semantic_consistency_gate_pass'] and c['all_NET_physical_node_type_switch_sequences_identical'] and c['packed_netlist_byte_identical']
 assert all(sha(k)==v for k,v in c['files'].items())
 work=parse((D/r['arm']/'native.log').read_text());assert work==r['native_work']
 assert int(re.findall(r'Total wirelength:\s*(\d+)',(D/r['arm']/'native.log').read_text())[-1])==r['wirelength']
trim=(D/'trim/native.log').read_text();assert rows[0]['exit_status']==1 and 'placement coordinates (59,55,0)' in trim and 'does not match given (60,55,0)' in trim
keys=['iterations','wirelength','diagnostic_cpd_ns','native_process_seconds']
delta={k:local[k]-raw[k] for k in keys}
for k in ['total_heap_pushes','total_rerouted_NET_operations','total_rerouted_connection_operations','printed_routing_seconds']:
 delta[k]=local['native_work'][k]-raw['native_work'][k]
summary={}
for r in [raw,local]:
 summary[r['arm']]={k:r[k] for k in keys};summary[r['arm']].update({k:v for k,v in r['native_work'].items() if k!='rows'});summary[r['arm']]['original_zero_counter_gate_pass']=r['canonical']['original_zero_counter_gate_pass']
result={'arms':summary,'trim_status':'FAILED_SEED_IMPORT_PLACEMENT_COORDINATE_MISMATCH','all_three_final_gates_pass':False,'raw_and_local_semantic_physical_canonical_pass':True,'local_minus_raw':delta,'decision':'Do not promote as native-work or end-to-end acceleration. Local reduces iterations and observed component runtime, but increases repeated NET/connection operations and wirelength. Trim failed before routing; no valid trim comparison. Preserve all arms and original partial rows.','limits':'One exposed MMC move, seed1, fixed order, prepared inputs/model/seeds unpaid; asynchronous CPD diagnostic only. Recovery canonical audit newly paid separately, not included in original native clock. No six-observation continuous timing, heldout family or hardware proof.','bindings':{str(x):sha(x) for x in [Path(__file__),D/'protocol.json',D/'rows.json',p,D/'trim/native.log',D/'raw/native.log',D/'local/native.log']}}
(D/'terminal_recovery_decision_v1.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
