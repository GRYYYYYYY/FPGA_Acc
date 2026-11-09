"""Re-serialize exact candidate content; unused diagnostic changes are explicit."""
import json,sys,hashlib
from pathlib import Path
from pre_route_endpoints import sha
from serialize_live_native_candidate import serialize
ROOT=Path(__file__).resolve().parents[1];i=int(sys.argv[1]);assert i in (0,2)
out=ROOT/'experiments/mux_heuristic_budget_cohort_2026-10-07';base=ROOT/'experiments/mux_owned_bound_cache_cohort_2026-10-06'
work=out/f'w8_m{i}';oldwork=base/f'w8_m{i}'
def read(p):return json.loads(p.read_text())
d=read(work/'result.json');old=read(oldwork/'result.json');p=read(out/'protocol.json');bp=read(base/'protocol.json')
assert p['cases']==bp['cases'] and p['binary_sha256']==bp['binary_sha256']
assert d['result']['status']=='COMPLETE_CANDIDATE' and d['result']['candidate']==old['result']['candidate'] and d['attempts']==old['attempts']
v=read(work/'native_input_verification.json');assert v['result_sha256']==sha(work/'result.json')
manifest=read(oldwork/'native_evidence_reuse.json');assert manifest['result_sha256']==sha(oldwork/'result.json')
assert all(sha(f)==h for f,h in manifest['cached_search_contracts'].items())
case=next(c for c in p['cases'] if (c['width'],c['index'])==(8,i));assert all(sha(f)==h for f,h in case['inputs'].items())
gate=ROOT/('experiments/mux_net_slack_focus_quality_gate_2026-10-06' if i==0 else 'experiments/mux_net_slack_w8m2_quality_gate_2026-10-06')
canonical=ROOT/('experiments/mux_net_slack_focus_candidate_canonical_2026-10-06' if i==0 else 'experiments/mux_net_slack_w8m2_candidate_canonical_2026-10-06')
assert manifest['gate_verification_sha256']==sha(gate/'verification.json') and manifest['candidate_canonical_verification_sha256']==sha(canonical/'verification.json')
gv=read(gate/'verification.json');cv=read(canonical/'verification.json');assert gv['receipt_sha256']==sha(gate/'receipt.json') and cv['receipt_sha256']==sha(canonical/'receipt.json')
assert all(sha(f)==h for row in read(canonical/'receipt.json')['rows'] for f,h in row['reload']['files'].items())
identity=gate/f'w8_m{i}/identity_probe/identity.jsonl';place=identity.parent/'design.place'
text,bindings=serialize(d['result']['candidate'],case['target'],identity,place)
assert text==(gate/f'w8_m{i}/predicted.route').read_text()
assert json.loads((gate/f'w8_m{i}/bindings.json').read_text())=={str(k):v for k,v in bindings.items()}
(work/'predicted.route').write_text(text)
assert cv['candidate_route_sha256']==sha(work/'predicted.route')
(work/'native_evidence_reuse.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),serializer_sha256=sha(ROOT/'tools/serialize_live_native_candidate.py'),result_sha256=sha(work/'result.json'),baseline_result_sha256=sha(oldwork/'result.json'),candidate_sha256=hashlib.sha256(json.dumps(d['result']['candidate'],sort_keys=True).encode()).hexdigest(),native_input_verification_sha256=sha(work/'native_input_verification.json'),old_native_manifest_sha256=sha(oldwork/'native_evidence_reuse.json'),predicted_route_sha256=sha(work/'predicted.route'),identity_sha256=sha(identity),place_sha256=sha(place),gate_verification_sha256=sha(gate/'verification.json'),candidate_canonical_verification_sha256=sha(canonical/'verification.json'),gate_selected=manifest['gate_selected'],candidate_cpd_ns=cv['candidate_cpd_ns'],scope='Full result files differ in unused alpha diagnostics. Candidate and actual staged updates identical; independently reserialized route bytes/bindings equal archived native input, own canonical files/proofs authenticated. Native CONTENT reuse, no new native execution/timers/publication.'),indent=2)+'\n');print('native candidate serialization parity',i)
