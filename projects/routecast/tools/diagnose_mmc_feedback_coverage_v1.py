"""Authenticate full development events and freeze a congestion-only ablation."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure

R = Path(__file__).resolve().parents[1]
D = R / 'experiments/ultraembedded_mmc_actual_old_linear_expat_workflow_v15_2026-10-10'
O = R / 'experiments/mmc_feedback_coverage_diagnostic_v1_2026-10-10'
bindings = closure([Path(__file__)])
for name in ['verification.json', 'stage_cost_verification_v12.json', 'undo_control_comparison_v4.json']:
    path = D / name
    proof = json.loads(path.read_text())
    for source, digest in proof['bindings'].items():
        assert sha(source) == digest, source
        bindings[source] = digest
    bindings[str(path)] = sha(path)
path = D / 'seed/model/mmc/receipt.json'
r = json.loads(path.read_text())
bindings[str(path)] = sha(path)
ep = D / 'seed/demand/mmc/endpoints.json'
endpoints = json.loads(ep.read_text())
bindings[str(ep)] = sha(ep)
nets = {q['net_id'] for q in endpoints['connections']}
assert len(endpoints['connections']) == 115572 and len(nets) == 55300
assert len(r['rounds']) == 2
rows = []
for round_ in r['rounds']:
    affected = round_['affected_nets']
    assert affected == sorted(set(affected)) and set(affected) <= nets
    assert [e['net_id'] for e in round_['events']] == affected
    rows.append(dict(round=round_['round_index'], affected_nets=len(affected),
                     affected_fraction=len(affected)/len(nets),
                     changed_nodes=len(round_['changed_nodes']),
                     overflow_before=round_['overflow_before'],
                     overflow_after=round_['overflow_after']))
assert set(r['rounds'][0]['affected_nets']) == nets
costs = {k:v for k,v in r.items() if k.endswith('_seconds')}
O.mkdir()
out = dict(bindings=bindings, complete_event_schedule_authenticated=True,
           total_nets=len(nets), required_connections=115572, rounds=rows, costs=costs,
           scope='Development diagnosis; model timers are nested, not additive. First-round full NET coverage is verified, not evidence of equivalent optimization or heldout speed.')
(O / 'diagnosis.json').write_text(json.dumps(out, indent=2) + '\n')
protocol = dict(bindings=bindings, status='PREREGISTERED_NOT_EXECUTED',
    development_case='mmc', control='actual-old linear undo model v13',
    candidate_rule='Remove fixed channel-span prices. Keep 50ps accumulated overflow prices, exact zero-price initial floors, all original endpoints, exactly two rounds, sorted affected NETs whose old ownership intersects changed overflow nodes, unchanged budget and fallback/atomic ledger/epoch rules.',
    mandatory_checks=['All 115572 initial and final connections retained',
                      'Independent XML/Fraction complete physical frame audits',
                      'Independent two-round affected-set/price/epoch/event replay',
                      'Failed replacement retains old whole-NET state',
                      'No historical predictions or native labels in candidate decisions',
                      'Full cold/seed native/canonical/ignored-pin and continuous cost gates'],
    decision='Retain quality regressions and negative time outcomes; do not adopt solely from reduced event count or overflow.',
    limitations='Development ablation, not strict heldout. No audit omission, sampling, stable timing or silicon claim.')
(O / 'candidate_protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
assert all(sha(k) == h for k,h in bindings.items())
print(json.dumps({k:v for k,v in out.items() if k!='bindings'}, indent=2))
