"""Authenticate exact cached-v5 and checked-v6 production outputs and round proofs."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments'
A=E/'adder_direct_from_inputs_cached_v5_2026-10-09';B=E/'adder_direct_from_inputs_checked_v6_2026-10-09'
D=E/'checked_cached_trajectory_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
bindings=closure([Path(__file__)])
for base in (A,B):
    p=base/'verification.json';v=json.loads(p.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
files=['result.json','terminal_sat.json']+[f'round_{i}.json' for i in range(87)]
for name in files:
    a=A/name;b=B/name
    assert json.loads(a.read_text())==json.loads(b.read_text()),name
    bindings[str(a)]=sha(a);bindings[str(b)]=sha(b)
assert all(sha(f)==h for f,h in bindings.items())
report=dict(bindings=bindings,compared_files=len(files),complete_result_and_round_proofs_equal=True,scope='Exact production candidate bank, events, rounds, final selection/model and proofs equality. Does not replace independent physical/formula/proof/native checks or paired timing.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('ALL89_PRODUCTION_ARTIFACTS_EQUAL')
