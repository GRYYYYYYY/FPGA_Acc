"""Bind unchanged full-cohort artifacts and preparation-only observed costs."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT = Path(__file__).resolve().parents[1]
old = ROOT/'experiments/mux_net_slack_budgets_2026-10-06'
new = ROOT/'experiments/mux_net_slack_incremental_budgets_2026-10-06'
def read(p):
    return json.loads(p.read_text())
a, b = read(old/'receipt.json'), read(new/'receipt.json')
checks = read(new/'transaction_checks.json')
assert checks == {'synthetic_transactions': 2000, 'real_trace_steps': 218, 'real_cases': 4, 'status': 'PASS'}
v = read(new/'verification.json')
assert v['receipt_sha256'] == sha(new/'receipt.json')
p = read(new/'protocol.json')
assert p['incremental_source_sha256'] == sha(ROOT/'tools/exact_incremental_timing_dag.py')
assert p['frozen_original_source_sha256'] == sha(ROOT/'tools/prepare_mux_net_slack_budgets.py')
assert read(old/'verification.json')['receipt_sha256'] == sha(old/'receipt.json')
assert len(a['rows']) == len(b['rows']) == 12
rows = []
for x, y in zip(a['rows'], b['rows']):
    w, i = x['width'], x['index']
    assert (w, i, x['status']) == (y['width'], y['index'], y['status'])
    af, bf = old/f'w{w}_m{i}.json', new/f'w{w}_m{i}.json'
    assert x['sha256'] == sha(af) == y['sha256'] == sha(bf)
    assert read(af) == read(bf)
    rows.append(dict(width=w, index=i, artifact_sha256=sha(bf),
                     original_seconds=x.get('preparation_seconds'),
                     incremental_seconds=y.get('preparation_seconds')))
(new/'equivalence_and_cost.json').write_text(json.dumps(dict(
    original_receipt_sha256=sha(old/'receipt.json'),
    incremental_receipt_sha256=sha(new/'receipt.json'),
    independent_verification_sha256=sha(new/'verification.json'),
    source_sha256=sha(Path(__file__)), transaction_checks_sha256=sha(new/'transaction_checks.json'), transaction_checker_sha256=sha(ROOT/'tools/check_exact_incremental_timing_dag.py'), rows=rows,
    scope='All12 output bytes, entire budgets/trace/skips unchanged. Single observed preparation timings only; no paired statistics, routing gain, native acceptance, or lifecycle speedup.'), indent=2)+'\n')
print(json.dumps(rows))
