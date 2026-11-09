"""Identify generated inputs still outside the prospective provided-route clock."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'provided_route_input_boundary_v1_2026-10-08';D.mkdir(exist_ok=False)
proof=E/'provided_raw_route_workflow_v1_2026-10-08/verification.json'
p=json.loads(proof.read_text());assert p['all_seven_measured_stages_terminal_zero']
assert all(sha(path)==digest for path,digest in p['bindings'].items())
canonical=E/'complete_wire_canonical_v2_2026-10-08/canonical'
original=R/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128'
target=E/'mux_budget_move_cohort_2026-10-06/w32_m2/target.place'
bindings={str(proof):sha(proof),str(Path(__file__)):sha(Path(__file__))}
rows=[]
for name in ('design.blif','design.net','design.place'):
 a=canonical/name;b=original/name
 bindings[str(a)]=sha(a);bindings[str(b)]=sha(b)
 row=dict(artifact=str(a),sha256=sha(a),original_artifact=str(b),
          same_bytes_as_original=sha(a)==sha(b),generation_inside_clock=False)
 if name=='design.place':
  bindings[str(target)]=sha(target);row['same_bytes_as_target_place']=sha(a)==sha(target)
 rows.append(row)
identity=canonical/'identity.jsonl';bindings[str(identity)]=sha(identity)
origin=E/'complete_wire_canonical_v2_2026-10-08/receipt.json'
o=json.loads(origin.read_text());assert all(sha(path)==digest for path,digest in o['bindings'].items())
bindings[str(origin)]=sha(origin)
assert not rows[1]['same_bytes_as_original'] and not rows[2]['same_bytes_as_target_place']
assert all(sha(path)==digest for path,digest in bindings.items())
out=dict(bindings=bindings,provided_route_workflow_seconds=p['provided_route_workflow_seconds'],
         native_entry_artifacts=rows,identity_artifact=str(identity),
         canonical_generation_origin=str(origin),
         symmetric_cold_cache_contract_proved=False,full_original_input_workflow_seconds=None,
         scope='Existing native entry uses previously generated canonical packed netlist/place/identity, including post-routing synchronization. Byte differences do not prove logical inequivalence; they do prove these are different input artifacts whose generation is outside this clock. Raw resume route, endpoints, budgets and fixed-local model generation also outside clock. Cannot treat all as free symmetric caches without declared provenance and same-start cold protocol.',
         next_action='Build identity at original supplied packed netlist and target placement; serialize fresh candidate against that identity and rerun native/canonical acceptance. Then extend upstream resume/seed creation and declare graph/model/budget cache costs symmetrically.')
(D/'manifest.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v for k,v in out.items() if k!='bindings'},flush=True)
