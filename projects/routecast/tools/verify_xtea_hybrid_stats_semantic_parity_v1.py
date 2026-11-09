"""Authenticate full development-case outputs against the original hybrid producer."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R = Path(__file__).resolve().parents[1]
old = R / 'experiments/resident_hybrid_complete_v5_2026-10-08/xtea/resident'
new = R / 'experiments/xtea_resident_hybrid_stats_v6_2026-10-09/xtea'
bindings = {str(Path(__file__)): sha(Path(__file__))}
for directory in [old, new]:
    receipt = directory / 'receipt.json'
    data = json.loads(receipt.read_text())
    for section in ['bindings', 'files']:
        assert all(sha(p) == h for p, h in data[section].items())
    bindings[str(receipt)] = sha(receipt)
    proof = directory / 'verification.json'
    verification = json.loads(proof.read_text())
    assert verification['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
    assert all(sha(p) == h for p, h in verification['bindings'].items())
    bindings[str(proof)] = sha(proof)

names = ['floors.json', 'initial.json', 'sketch.json', 'round0.json', 'round1.json']
for name in names:
    left, right = old / name, new / name
    assert json.loads(left.read_text()) == json.loads(right.read_text()), name
    bindings.update({str(left): sha(left), str(right): sha(right)})
rounds = [json.loads((p / 'receipt.json').read_text())['rounds'] for p in [old, new]]
assert len(rounds[0]) == len(rounds[1]) == 2
for a, b in zip(*rounds):
    # Only machine-local frame paths and diagnostic elapsed times are excluded.
    assert {k: v for k, v in a.items() if k not in ['state_file', 'seconds']} == {
        k: v for k, v in b.items() if k not in ['state_file', 'seconds']}
assert all(sha(p) == h for p, h in bindings.items())
result = dict(bindings=bindings, complete_outputs_and_all_event_semantics_equal=True,
              compared_frames=names, compared_rounds=2,
              scope='Full archived XTEA development-case parity only. Instrumentation does not establish MMC parity, heldout accuracy, stable speedup or complete workflow gain.')
(new / 'semantic_parity_verification.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS complete XTEA frames and events semantic parity')
