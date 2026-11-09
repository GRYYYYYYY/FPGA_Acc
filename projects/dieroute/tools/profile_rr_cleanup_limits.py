"""Explain audited cleanup outcomes; rejected candidates are not realizable gains."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from profile_rr_wirelength_regression import profile

root = Path(__file__).resolve().parents[1]
audit_path = root/'work/rr_wide_cleanup_variant_20261014/independent_audit.json'
audit = json.loads(audit_path.read_text())['experiments'][0]
result = audit['modes']['downstream_bounded']
assert result['status'] == 'passed' and result['repeats_verified'] == 5
pair = Path(audit['manifest']).parent
case = Path(audit['case'])
sources = [audit_path, Path(audit['manifest']), Path(__file__)]
reference_rows = None
for repeat in range(5):
    path = pair/f'downstream_bounded_{repeat}.cleanup.csv'
    sources.append(path)
    with path.open() as stream:
        rows = [{k:int(v) for k,v in row.items()} for row in csv.DictReader(stream)]
    if reference_rows is None:
        reference_rows = rows
    assert rows == reference_rows
groups = {}
accepted_by_net = Counter()
for row in reference_rows:
    complete, feasible, delay = (row[k] for k in ('complete','feasible','delay_ok'))
    lower = row['candidate_wire'] < row['old_wire']
    assert row['accepted'] == int(bool(complete and feasible and delay and lower))
    if not row['accepted']:
        assert row['before_hash'] == row['after_hash']
    reason = ('accepted' if row['accepted'] else 'incomplete' if not complete else
              'capacity_rejected' if not feasible else 'delay_rejected' if not delay else
              'no_strict_wire_improvement')
    group = groups.setdefault(str(row['pass']), {})
    entry = group.setdefault(reason, dict(attempts=0, shorter_candidates=0,
                                         candidate_reduction_sum=0))
    entry['attempts'] += 1
    entry['shorter_candidates'] += int(lower)
    # Counts observed proposals, potentially repeating a net across passes.
    entry['candidate_reduction_sum'] += max(0,row['old_wire']-row['candidate_wire'])
    if row['accepted']:
        accepted_by_net[row['net_id']] += row['old_wire']-row['candidate_wire']
metrics = result['counters']
assert sum(accepted_by_net.values()) == metrics['cleanup_wirelength_before']-metrics['cleanup_wirelength_after']
assert sum(r['accepted'] for r in reference_rows) == metrics['cleanup_accepted_nets']
terminal = profile(case,pair)
assert terminal['candidate_wirelength'] == result['native_qor']['total_wirelength']
assert terminal['baseline_wirelength'] == result['native_qor']['baseline_wirelength']
for row in terminal['net_deltas']:
    row['accepted_cleanup_reduction'] = accepted_by_net[row['net_id']]
    row['pre_cleanup_wire'] = row['candidate']+row['accepted_cleanup_reduction']
assert sum(r['pre_cleanup_wire'] for r in terminal['net_deltas']) == metrics['cleanup_wirelength_before']
sources += [case/'rr_graph.xml',case/'circuit.route',pair/'downstream_bounded.route']
report = dict(status='five_repeat_cleanup_limits_profiled',by_pass=groups,
              accepted_reduction=sum(accepted_by_net.values()),
              final_baseline_excess=terminal['candidate_wirelength']-terminal['baseline_wirelength'],
              net_deltas=terminal['net_deltas'],
              source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
              scope='One audited CPU development case. Delay flags use local path-delay guards, not native STA. Rejected proposal sums are not achievable or additive QoR gains. Matched-source control pending.',
              board_result=False,research_complete=False)
output=root/'work/rr_cleanup_limits_profile_20261014.json'
assert not output.exists(), 'Preserve previous evidence'
output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('status','by_pass','accepted_reduction','final_baseline_excess')}))
