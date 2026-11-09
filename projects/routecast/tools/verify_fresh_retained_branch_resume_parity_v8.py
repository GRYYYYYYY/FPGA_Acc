"""Complete fresh-resume physical state identity, with reproducible verifier binding."""
import json
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'fresh_retained_branch_resume_v7_2026-10-08';old=E/'native_resume_branch_partial_v8_2026-10-08'
bindings={str(Path(__file__)):sha(Path(__file__))}
for parent in (D,old):
 path=parent/'physical_endpoint_verification.json';obj=json.loads(path.read_text())
 assert obj['all_target_connections_physical_endpoint_pass'] and obj['connections']==1929
 assert all(sha(name)==digest for name,digest in obj['bindings'].items())
 bindings.update(obj['bindings']);bindings[str(path)]=sha(path)
def norm(path):return Counter((name,branch) for name,branches in physical_paths(path).items() for branch in branches)
assert norm(D/'resume/output.route')==norm(old/'resume/output.route')
seed=E/'fresh_retained_branch_seed_v7_2026-10-08/verification.json';proof=json.loads(seed.read_text())
assert proof['all1929_retained_release_decisions_and_physical_fraction_witnesses_equal']
assert all(sha(name)==digest for name,digest in proof['bindings'].items())
bindings.update(proof['bindings']);bindings[str(seed)]=sha(seed)
r=json.loads((D/'receipt.json').read_text());assert r['rows'][0]['loaded_tree_marker']
assert all(sha(name)==digest for name,digest in bindings.items())
out=dict(bindings=bindings,all1929_fresh_resume_physical_paths_equal_historical=True,
 native_resume_wall_seconds=r['rows'][0]['wall_seconds'],
 scope='Actual fresh seed resume and complete original XML physical/endpoints audit. Entire route equality authenticates prior physical/RC evidence, not new canonical/HDL equivalence or a combined workflow clock. Missing65 does not imply only65 rerouting attempts.')
(D/'parity_verification_v2.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v for k,v in out.items() if k!='bindings'},flush=True)
