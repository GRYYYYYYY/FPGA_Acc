"""Describe matched first-pass mechanism evidence; no replacement utility gate."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
D=R/'experiments/mmc_partial_firstpass_recovery_v3_2026-10-18';p=D/'independent_wire_work_comparison_v1.json';v=json.loads(p.read_text());assert v['status']=='pass' and v['all6_independent_wire_and_every_iteration_integer_fields_equal'];assert all(sha(q)==h for q,h in v['bindings'].items());rows=[]
for r in v['rows']:
 off=r['observations']['off'];on=r['observations']['on'];a=off['first_iteration'];b=on['first_iteration']
 rows.append(dict(case=r['case'],first_iteration_connection_operations=dict(off=a['rerouted_connection_operations'],on=b['rerouted_connection_operations']),first_iteration_connection_operations_lower=b['rerouted_connection_operations']<a['rerouted_connection_operations'],total_heap_reduction=r['heap_reduction'],on_minus_off=r['on_minus_off'],wire_nonregression=on['wirelength']<=off['wirelength'],printed_diagnostic_CPD_nonregression=on['diagnostic_cpd_ns']<=off['diagnostic_cpd_ns']))
result=dict(status='controlled_exposed_mechanism_ablation_verified',bindings={**v['bindings'],str(p):sha(p),str(Path(__file__).resolve()):sha(Path(__file__).resolve())},rows=rows,all3_first_iteration_connection_operations_lower=all(r['first_iteration_connection_operations_lower'] for r in rows),all3_total_heap_lower=all(r['total_heap_reduction']>0 for r in rows),all3_wire_nonregression=all(r['wire_nonregression'] for r in rows),all3_printed_diagnostic_CPD_nonregression=all(r['printed_diagnostic_CPD_nonregression'] for r in rows),scope='Same inputs and seeds, opt-in first-pass partialNET preservation only; native FULL/115572query physical/canonical admitted and independent integer/wire replay. Exposed cases only; canonical ignored-pin fixups are not a zero-counter pass. No alteration of failed15arm utility/forecast gate, no fresh end-to-end timing, full STA, heldout or FPGA proof.')
with (D/'research_decision_v2.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:x for k,x in result.items() if k!='bindings'}),flush=True)
