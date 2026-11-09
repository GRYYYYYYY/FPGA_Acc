"""Authenticate both independent audit reports and compare complete coverage rows."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'adder_online_conflict_audit_parity_v1_2026-10-09';D.mkdir(exist_ok=False)
reports=[E/f'adder_online_conflict_branch_verification_v{v}_2026-10-09/verification.json' for v in (1,2)]
docs=[json.loads(p.read_text()) for p in reports]
bindings=closure([Path(__file__)])
for p,doc in zip(reports,docs):
 bindings[str(p)]=sha(p)
 for path,digest in doc['bindings'].items():
  assert sha(path)==digest
  assert path not in bindings or bindings[path]==digest
  bindings[path]=digest
assert docs[0]['rows']==docs[1]['rows']
assert sum(r['generated_paths_independent_fraction_capacity_parent_pass'] for r in docs[1]['rows'])==13621
assert sum(r['diagnostic_witnesses_fraction_owner_replay_pass'] for r in docs[1]['rows'])==169
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=docs[1]['rows'],scope='Authenticated same-corpus audit coverage parity, incremental touched-node checks plus full terminal state reconstruction. No new search or measured workflow speedup.'),indent=2)+'\n')
print('Both audit source/input closures authenticated; 13621 paths and 169 witnesses coverage parity passed.')
