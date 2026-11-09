"""Authenticate full development-case outputs against the original hybrid producer."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R = Path(__file__).resolve().parents[1]
old = R / 'experiments/mmc_resident_hybrid_stats_v6_2026-10-09/mmc'
new = R / 'experiments/mmc_resident_prepriced_stats_v7_2026-10-09/mmc'
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

branch_proof = new / 'branch_work_verification.json'
branch = json.loads(branch_proof.read_text())
assert branch['all_search_records_match_full_original_NET_phase_and_dispatch']
assert all(sha(p) == h for p, h in branch['bindings'].items())
bindings[str(branch_proof)] = sha(branch_proof)

receipts = [json.loads((directory / 'receipt.json').read_text()) for directory in [old, new]]
endpoints = [next(Path(p) for p in r['bindings'] if p.endswith('/endpoints.json')) for r in receipts]
assert sha(endpoints[0]) == sha(endpoints[1])
assert json.loads(endpoints[0].read_text()) == json.loads(endpoints[1].read_text())
bindings.update({str(p): sha(p) for p in endpoints})

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
work = [json.loads((directory / 'search_work.json').read_text()) for directory in [old, new]]
assert work[0]['initial_queries'] == work[1]['initial_queries']
assert work[0]['round_queries'] == work[1]['round_queries']
assert len(work[0]['metrics']) == len(work[1]['metrics'])
for left, right in zip(work[0]['metrics'], work[1]['metrics']):
    assert {k: v for k, v in left.items() if k != 'seconds'} == {k: v for k, v in right.items() if k != 'seconds'}
for directory in [old, new]:
    file = directory / 'search_work.json'
    bindings[str(file)] = sha(file)

assert all(sha(p) == h for p, h in bindings.items())
result = dict(bindings=bindings, complete_outputs_and_all_event_semantics_equal=True, all_search_dispatch_and_reported_counts_equal=True,
              compared_frames=names, compared_rounds=2,
              scope='Full original MMC development-case parity only. No heldout accuracy, stable speedup or complete workflow gain.')
(new / 'semantic_parity_verification.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS complete MMC prepared-price frames/events/reported work parity')
