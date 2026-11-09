"""Authenticate actual timed acceptance stages, outputs and bounded fee scope."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
E=R/'experiments'
D=E/'raw_candidate_native_chain_v1_2026-10-08'
r=json.loads((D/'receipt.json').read_text())
p=json.loads((D/'protocol.json').read_text())
assert sha(D/'protocol.json')==r['protocol_sha256']
assert all(sha(path)==digest for path,digest in r['bindings'].items())
assert [stage['script'] for stage in r['stages']]==p['stages']
assert len(r['stages'])==4 and all(stage['exit_code']==0 and stage['elapsed_seconds']>0 for stage in r['stages'])
covered=sum(stage['elapsed_seconds'] for stage in r['stages'])
assert covered<=r['component_elapsed_seconds']
bindings={**r['bindings'],str(D/'receipt.json'):sha(D/'receipt.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__)):sha(Path(__file__))}
for stage in r['stages']:
 path=D/(stage['script']+'.log');bindings[str(path)]=sha(path)
for path in (E/'raw_candidate_native_reload_v1_2026-10-08/verification.json',
             E/'raw_candidate_canonical_v1_2026-10-08/verification.json',
             E/'raw_candidate_native_reload_v1_2026-10-08/native_quality_verification.json'):
 obj=json.loads(path.read_text())
 assert all(sha(name)==digest for name,digest in obj['bindings'].items())
 bindings.update(obj['bindings']);bindings[str(path)]=sha(path)
 if path.name=='native_quality_verification.json':
  assert obj['full_chain_pass'] and obj['joint_quality_pass']
  assert obj['initial_fixups']==99 and obj['canonical_fixups']==0
quality=obj
assert all(sha(path)==digest for path,digest in bindings.items())
out=dict(bindings=bindings,all_four_actual_native_acceptance_and_audit_stages_terminal_zero=True,
         stages=r['stages'],component_elapsed_seconds=r['component_elapsed_seconds'],
         residual_seconds=r['component_elapsed_seconds']-covered,
         cpd_ns=quality['cpd_ns'],wirelength=quality['wirelength'],
         initial_fixups=99,canonical_fixups=0,full_workflow_seconds=None,
         scope='Prospective native component clock includes serialization, process startup, FULL STA reload, post-sync Fraction audit, canonical zero-fixup reload, canonical physical audit and their JSON outputs. Quality comparison and this cost verifier outside clock. Starts with a provided verified candidate; cannot add to separately timed producer as a measured single workflow. Upstream generation, candidate clock gaps/final serialization, original HDL equivalence, all-budget admission, unseen-family and paired speedup remain unresolved.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v for k,v in out.items() if k!='bindings'},flush=True)
