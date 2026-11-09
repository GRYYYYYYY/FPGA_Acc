"""Close the full large pilot with authenticated clock scopes and no paired claim."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/neuron_quotient_raw_floor_pilot_v1_2026-10-17';L=R/'experiments/neuron_raw_floor_pilot_launch_v1_2026-10-17'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
p=D/'verification.json';d=json.loads(p.read_text());owner=json.loads((L/'verification.json').read_text());terminal=json.loads((L/'terminal.json').read_text());m=json.loads((L/'process.json').read_text());proc=Path('/proc')/str(m['pid'])/'stat'
if proc.exists():assert proc.read_text().rsplit(')',1)[1].split()[19]!=m['start_stat'].rsplit(')',1)[1].split()[19]
assert owner['large_pilot_complete'] and terminal['exit_status']==0 and terminal['child_address_space_limit_bytes']==20*2**30
for v in [d,owner]:
 for k,h in v['bindings'].items():assert sha(k)==h
assert d['all77106_exact_archived_floors_original_XML_Fraction_RC_and_singleparents_pass'] and d['connections']==77106 and d['NETs']==50767
assert sha(D/'paths.json')==d['paths_sha256']
major=['load_and_authentication_seconds','quotient_graph_setup_seconds','search_reconstruction_validation_seconds','independent_XML_audit_and_final_auth_seconds'];assert abs(sum(d[k] for k in major)-d['total_seconds'])<0.1
out=dict(bindings={str(x):sha(x) for x in [Path(__file__).resolve(),p,L/'verification.json',L/'terminal.json']},all_pass=True,all77106floors_and_paths_closed=True,NETs=50767,changed_equal_cost_initial_paths=d['changed_equal_cost_initial_paths'],phase_seconds={k:d[k] for k in major},total_pilot_seconds=d['total_seconds'],nested_expand_calls_seconds=d['all_expand_calls_seconds'],clock_scope='Final phase also contains cache reporting/native teardown/GC/path serialization, not pure XML audit. Expand clocks include cold table misses; lower-table time is nested again. Never sum these nested clocks.',decision='Admit one frozen full neuron raw-floor model/all3audits/all8metrics trial. No default promotion and no paired large-design or end-to-end speedup claim.',quality_risk='1667equal-cost initial paths differ. Exact floors and numeric budgets do not preserve demand or feedback trajectory; small XTEA full-model quality was mixed.',goal_complete=False)
with (D/'research_decision_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
