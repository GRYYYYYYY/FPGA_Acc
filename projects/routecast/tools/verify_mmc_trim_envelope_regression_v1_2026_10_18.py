"""Actual failed-seed regression: full native envelope differs, paths identical."""
import json
from pathlib import Path
from audit_native_route import NET
from native_route_ledger_import_compact import physical_paths
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_trim_envelope_regression_v1_2026-10-18';D.mkdir(exist_ok=False);old=R/'experiments/mmc_native_trim_seed_v1_2026-10-18/seed.route';new=R/'experiments/mmc_native_trim_seed_v2_2026-10-18/seed.route';log=R/'experiments/mmc_native_seed_utility_pilot_v1_2026-10-18/trim/native.log'
def check(path):
 for line in path.read_text().splitlines():
  if line.startswith('Net ') and not NET.match(line):raise ValueError('nonphysical/global NET section')
  if line.startswith('Block '):raise ValueError('stale global Block metadata')
try:check(old)
except ValueError as e:reason=str(e)
else:raise AssertionError('Old native-rejected envelope accepted')
check(new);assert physical_paths(old)==physical_paths(new);assert 'placement coordinates (59,55,0)' in log.read_text()
with (D/'verification.json').open('x') as f:json.dump(dict(bindings={str(p):sha(p) for p in [Path(__file__),old,new,log]},old_native_rejected_seed_fails_new_envelope_gate=True,rejection=reason,repaired_seed_passes_envelope_gate=True,all_physical_paths_identical=True,scope='Actual failed native input regression for chosen physical-only partial seed format; full graph/path/pin/capacity proof remains separate.'),f,indent=2);f.write('\n')
print('PASS actual failed envelope rejected, repaired envelope accepted, all paths identical')
