"""Authenticate all owner stages/certificates and nonoverlapping phase accounting."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'profile_native_owner_potential_only_v2_2026-10-08';B=E/'fresh_critical_owner_transactions_v1_2026-10-08';bindings={}
def read(path):
 obj=json.loads(path.read_text())
 for name,digest in obj.get('bindings',{}).items():
  assert sha(name)==digest,name
  assert name not in bindings or bindings[name]==digest
  bindings[name]=digest
 bindings[str(path)]=sha(path);return obj
r=read(D/'receipt.json');assert r['potential_native_calls']==102 and r['potential_fallback_calls']==0
old=read(B/'receipt.json');proof=read(B/'parity_verification.json')
assert proof['all4_candidates_and102_stage_paths_equal_historical_native_validated_states']
assert len(r['rows'])==len(old['rows'])==4
total=0
for left,right in zip(r['rows'],old['rows']):
 for key in ('plan','state','transaction_complete','published','critical_delay_improved'):assert left[key]==right[key],key
 assert len(left['events'])==len(right['events'])
 for a,b in zip(left['events'],right['events']):
  assert {k:v for k,v in a.items() if k not in ('certificate','certificate_sha256')}=={k:v for k,v in b.items() if k not in ('certificate','certificate_sha256')}
  assert sha(a['certificate'])==a['certificate_sha256']
  assert json.loads(Path(a['certificate']).read_text())==json.loads(Path(b['certificate']).read_text())
 total+=len(left['events'])
assert total==102
assert 'python_reference_potential_check' not in r['phase_calls']
ref=read(R/'experiments/profile_native_owner_potential_check_v2_2026-10-08/verification.json')
assert ref['all4_candidates_and102_stage_paths_certificate_contents_equal']
assert ref['phase_calls']['python_reference_potential_check']==102
for name in ('search','native_potential_check','certificate_json_and_hash'):assert r['phase_calls'][name]==102
assert r['phase_calls']['complete_state_frame']==4 and r['phase_calls']['progress_output']==4
covered=r['setup_seconds']+sum(r['phases_seconds'].values());assert 0<=covered<=r['component_elapsed_seconds']
bindings[str(Path(__file__))]=sha(Path(__file__))
assert all(sha(path)==digest for path,digest in bindings.items())
out=dict(bindings=bindings,all4_candidates_and102_stage_paths_certificate_contents_equal=True,native_calls=r['native_calls'],fallback_calls=r['fallback_calls'],
 component_elapsed_seconds=r['component_elapsed_seconds'],setup_seconds=r['setup_seconds'],
 phases_seconds=r['phases_seconds'],phase_calls=r['phase_calls'],residual_seconds=r['component_elapsed_seconds']-covered,
 full_workflow_seconds=None,scope='All physical paths, original budgets, atomic transaction results and exact clipped-potential contents match independently certified full four-owner production. Timers are disjoint; frame wrapper measures four final complete frames; release/restore ledger operations measured separately. One standalone component observation, not paired or end-to-end gain; upstream generation and downstream wire/native plus final receipt output excluded.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'},flush=True)
