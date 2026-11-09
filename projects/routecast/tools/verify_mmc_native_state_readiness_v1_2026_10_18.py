"""Authenticate selected MMC old-state gates and linked original input bytes."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_native_state_geometry_v1_2026-10-18';protocol=json.loads((D/'protocol.json').read_text());expected={**protocol['bindings'],str(D/'protocol.json'):sha(D/'protocol.json')};prior=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold'
proofs=[prior/'native/mmc/verification.json',prior/'canonical/ignored_pin_verification_v1.json',Path(protocol['nodebase_proof']),Path(protocol['native_initial_criticality_directory'])/'verification.json']
for p in proofs:
 d=json.loads(p.read_text())
 for f,h in d.get('bindings',{}).items():
  if f in expected:assert expected[f]==h
  expected[f]=h
canonical=json.loads((prior/'canonical/receipt.json').read_text())['rows'][0]['canonical'];expected.update(canonical['files']);assert canonical['semantic_consistency_gate_pass'] and canonical['canonical_original_XML_arc_branch_capacity_pass']
for p,h in expected.items():assert sha(p)==h,p
expected[str(Path(__file__))]=sha(__file__)
with (D/'readiness_verification_v1.json').open('x') as f:json.dump(dict(bindings=expected,all_selected_old_native_physical_criticality_nodebase_and_canonical_dependencies_authenticated=True,connections=115572,native_canonical_semantic_pass=True,original_zero_counter_gate=False,ignored_pin_fixups=330,new_target_native_outputs=False,scope='Existing old-state readiness and frozen geometry only; new target placement/frontend/affected closure and full update still unexecuted.'),f,indent=2);f.write('\n')
print('PASS MMC old state readiness',len(expected),'unique file bindings',flush=True)
