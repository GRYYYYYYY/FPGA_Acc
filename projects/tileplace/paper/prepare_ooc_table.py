#!/usr/bin/env python3
"""Regenerate the audited October 12--14 internal OOC experiment table.

This table preserves failed timing candidates. It does not select an adopted
implementation or combine correctness evidence across candidates.
"""
import argparse
import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_full_color_routed_ooc import audit, digest


EXPERIMENTS = [
    ('Owners return wait', 'owners_wait_routed_preload_recovery_2026-10-12'),
    ('Trial equality protocol', 'trial_equal_protocol_clocked_routed_attempt02_2026-10-12'),
    ('Commit find comparison', 'commit_find_compare_clocked_routed_2026-10-12'),
    ('Trial offset validation', 'build_offsets_trial_validation_clocked_routed_2026-10-12'),
    ('Best unit validation', 'best_unit_validation_clocked_routed_2026-10-12'),
    ('Identity kind count', 'identity_kind_count_clocked_routed_2026-10-12'),
    ('Translation index return', 'translate_initial_index_return_clocked_routed_2026-10-13'),
    ('Identity kind nonzero', 'identity_kind_nonzero_clocked_routed_2026-10-13'),
    ('Roots shift end', 'roots_shift_end_clocked_routed_2026-10-13'),
    ('Eligible validation index', 'eligible_validation_index_clocked_routed_2026-10-13'),
    ('Trial location inline', 'trial_location_inline_clocked_routed_2026-10-13'),
    ('Encode status return', 'encode_status_return_clocked_routed_2026-10-13'),
    ('Best dimension guard', 'best_dimension_guard_clocked_routed_2026-10-13'),
    ('Roots page guard', 'roots_page_guard_clocked_routed_2026-10-13'),
    ('Identity member nonzero', 'identity_member_nonzero_clocked_routed_2026-10-13'),
    ('Cost position compare', 'cost_position_compare_clocked_routed_2026-10-13'),
    ('Selection member return', 'selection_member_return_clocked_routed_2026-10-13'),
    ('Commit find return', 'commit_find_return_clocked_routed_2026-10-13'),
    ('Position entry ID', 'position_entry_id_clocked_routed_2026-10-13'),
    ('Position condition return', 'position_condition_return_clocked_routed_2026-10-13'),
    ('Position remaining span', 'position_remaining_span_clocked_routed_2026-10-13'),
    ('Position ID compare return', 'position_id_compare_return_clocked_routed_2026-10-14'),
]


def prepare(output):
    rows = []
    for label, name in EXPERIMENTS:
        package = ROOT / 'work' / name
        checked = audit(package)
        prior_path = package / 'independent_routed_audit.json'
        prior = json.loads(prior_path.read_text())
        # Compare every stable field, including source/output identities and
        # detailed paths, rather than accepting a prior PASS/FAIL label alone.
        for key, value in checked.items():
            if key != 'observed_at_utc':
                assert prior[key] == value, (name, key)
        rows.append({
            'label': label, 'package': str(package.relative_to(ROOT)),
            'terminal_sha256': digest(package / 'attempt_01_terminal.json'),
            'prior_audit_sha256': digest(prior_path), 'fresh_audit': checked,
        })
        print(label, checked['wns_ns'], flush=True)
    lines = [r'\begin{tabular}{lrrrl}', r'\toprule',
             r'Candidate & WNS (ns) & TNS (ns) & Setup fails & Gate \\',
             r'\midrule']
    for row in rows:
        a = row['fresh_audit']
        gate = 'Pass' if a['internal_timing_route_drc_pass'] else 'Fail'
        lines.append(f"{row['label']} & {a['wns_ns']:.3f} & {a['tns_ns']:.3f} & "
                     f"{a['setup_failing_endpoints']} & {gate} " + r'\\')
    lines.extend([r'\bottomrule', r'\end{tabular}', ''])
    output.mkdir(parents=True, exist_ok=True)
    table = output / 'ooc_experiments_table.tex'
    table.write_text('\n'.join(lines))
    compact = [r'\begin{tabular}{lrrr}', r'\toprule',
               r'Candidate & WNS & TNS & Fails \\', r'\midrule']
    for row in rows:
        a = row['fresh_audit']
        compact.append(f"{row['label']} & {a['wns_ns']:.3f} & {a['tns_ns']:.3f} & "
                       f"{a['setup_failing_endpoints']} " + r'\\')
    compact.extend([r'\bottomrule', r'\end{tabular}', ''])
    compact_table = output / 'ooc_experiments_compact_table.tex'
    compact_table.write_text('\n'.join(compact))
    metadata = {
        'schema': 'TILEPLACE_OOC_EXPERIMENT_TABLE_V1',
        'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': f'{len(rows)} terminal October 12--14 internal 4 ns OOC experiments; '
                 'not an exhaustive history, functional adoption, or board result',
        'source_audits_pass': True,
        'timing_pass_count': sum(r['fresh_audit']['internal_timing_route_drc_pass'] for r in rows),
        'generator_sha256': digest(Path(__file__)),
        'table_sha256': digest(table),
        'compact_table_sha256': digest(compact_table), 'experiments': rows,
        'limitations': ['The October 4 functional baseline is separate.',
                        'Live candidates and separate post-route physical variants are excluded.',
                        'Rows are separate implementations, not a causal ablation.',
                        'OOC input/output delay closure and physical execution are unproven.'],
    }
    (output / 'ooc_experiments_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'paper/generated')
    result = prepare(parser.parse_args().output.resolve())
    print(json.dumps({'audited_experiments': len(result['experiments']),
                      'timing_pass_count': result['timing_pass_count']}))
