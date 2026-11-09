"""Read-only audit of native seed bindings and materialized rebound tables."""
import json
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/gf2_bound_identity_reuse_2026-10-06'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json')
assert all(sha(path)==h for path,h in p['sources'].items())
assert p['parent_protocol_sha256']==sha(ROOT/'experiments/gf2_identity_rebinding_fresh_2026-10-06/protocol.json')
assert [c['width'] for c in r['cases']]==[32,64,128]
count=0
for c in r['cases']:
    seed=Path(c['seed']);assert sha(seed)==c['seed_sha256']
    s=json.loads(seed.read_text());native=Path(s['native_receipt'])
    assert sha(native)==s['native_receipt_sha256']
    proof=json.loads(native.read_text())
    assert proof['exit_code']==1 and proof['bindings']['inputs_sha256']==s['bindings']['sha256']
    assert all(sha(path)==s['bindings']['sha256'][name] for name,path in s['bindings']['files'].items())
    assert sha(s['table'])==s['table_sha256']==proof['table_sha256']
    assert sha(s['log'])==s['log_sha256']==proof['log_sha256']
    rebound=seed.parent/'rebound.json'
    assert sha(rebound)==c['rebound_sha256'] and sha(c['target'])==c['target_sha256']
    a=json.loads(rebound.read_text());b=[json.loads(line) for line in Path(c['target']).read_text().splitlines()]
    assert a==b
    count+=sum(len(row['pins']) for row in a)
    assert c['rejected']==['binary','architecture','blif','net','graph','seed_receipt']
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),native_seeds_checked=3,rebound_pins_checked=count,scope='Independent hash/native proof binding and materialized parity audit. Negative rejection probes producer-only. No route/STA, general equivalence or timing benefit proof.'),indent=2)+'\n')
print('verified',count,'pins')
