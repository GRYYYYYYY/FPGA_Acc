"""Full4 matched native commands and canonical QoR/budget comparison, no runtime claim."""
import json
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_reverse_group_quality_v1_2026-10-08';D.mkdir(exist_ok=False)
roots={a:E/name for a,name in [('seed','adder_reverse_group_native_reload_v1_2026-10-08'),('cold','adder_wire_guard_matched_cold_v4_2026-10-08'),('seed_canonical','adder_reverse_group_canonical_reload_v1_2026-10-08'),('cold_canonical','adder_wire_guard_matched_cold_canonical_v4_2026-10-08')]};docs={};bindings={}
for arm,root in roots.items():
 for name in ('protocol.json','receipt.json'):
  p=root/name;doc=json.loads(p.read_text());assert all(sha(f)==h for f,h in doc['bindings'].items());bindings.update(doc['bindings']);bindings[str(p)]=sha(p);docs[arm+'_'+name]=doc
rows=[]
for i in range(4):
 sp=docs['seed_protocol.json']['plans'][i];cp=docs['cold_protocol.json']['plans'][i];assert all(sp[k]==cp[k] for k in ('step','command','endpoints','budget'))
 a=docs['seed_receipt.json']['rows'][i];b=docs['cold_receipt.json']['rows'][i]
 assert a['loaded'] and not b['loaded'] and a['exit_code']==b['exit_code']==0 and a['full_check'] and b['full_check']
 for arm in ('seed_canonical','cold_canonical'):
  x=docs[arm+'_receipt.json']['rows'][i];assert x['original_zero_counter_gate_pass'] and x['semantic_consistency_gate_pass'] and x['all516_named_paths_equal']
 rows.append(dict(step=i,seed_cpd_ns=a['cpd_ns'],cold_cpd_ns=b['cpd_ns'],seed_wire=a['wirelength'],cold_wire=b['wirelength'],joint_printed_nonregression=F(a['cpd_ns'])<=F(b['cpd_ns']) and a['wirelength']<=b['wirelength'],seed_budget_failures=len(a['violation_ids']),cold_budget_failures=len(b['violation_ids']),new_failed_connection_ids=sorted(set(a['violation_ids'])-set(b['violation_ids'])),repaired_connection_ids=sorted(set(b['violation_ids'])-set(a['violation_ids']))))
bindings[str(Path(__file__))]=sha(Path(__file__))
report=dict(bindings=bindings,rows=rows,all4_canonical_zero_full_sta_pass=True,total_seed_budget_failures=sum(x['seed_budget_failures'] for x in rows),total_cold_budget_failures=sum(x['cold_budget_failures'] for x in rows),scope='Same4 inputs/commands/binary/options actual seeded versus new cold, all canonical zero mismatch/fixup FULL/STA verified. Candidate preparation, serialization and audit costs not measured as paired workflow; no userclock/HDL/unseen-family or runtime-gain proof. All per-CID budget regressions retained.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='bindings'},indent=2))
