#!/usr/bin/env python3
"""Recheck frozen CPU framework evidence without repeating measured runs.

This verifies the bytes underlying completed publication audits, not a new native
P&R execution or proof of research benefit. Unsupported inputs remain failures.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from audit_development import require
from run_development import ROOT, sha
from summarize_independent_validation import binding, checked, summarize


def recheck(summary_path):
    saved = json.loads(summary_path.read_text())
    study_path = checked(saved['study'])
    require(summarize(study_path) == saved, 'saved summary differs from frozen evidence')
    study = json.loads(study_path.read_text())
    freeze = json.loads(checked(study['freeze']).read_text())
    # Test evidence is applicable to today's implementation only if those
    # implementation bytes still match the measured cohort.
    for entry in freeze['sources']:
        checked(entry)
    protocol = json.loads(checked(study['protocol']).read_text())
    expected = {(d, t['id']) for d in protocol['designs'] for t in protocol['tracks']}
    require({(r['design'], r['track']) for r in study['rows']} == expected,
            'selected design/track population differs')
    rows = []
    for row in study['rows']:
        root = Path(row['directory'])
        outer = root.parent / (row['track'] + '_process.process.json')
        require(json.loads(outer.read_text()) == row['process'], 'outer process receipt differs')
        processes = []
        for name in ('configure', 'build_command', 'tests', 'prepare'):
            p = root / (name + '.process.json')
            record = json.loads(p.read_text())
            for stream in ('stdout', 'stderr'):
                require(sha(root / (name + '.' + stream + '.log')) == record[stream + '_sha256'],
                        'changed subprocess output: ' + str(p))
            expected_exit = 1 if name == 'prepare' and not row['completed'] else 0
            require(record['exit_status'] == expected_exit, 'unexpected build/test/prepare failure')
            require(record['wall_ns'] > 0, 'missing failed or successful process cost')
            processes.append(binding(p))
        test_log = root / 'build/Testing/Temporary/LastTest.log'
        text = test_log.read_text()
        require(text.count('Test Passed.') == 3 and
                'PASS (113 checks, real PR HBM C-model)' in text and
                'Ran 6 tests' in text, 'wrong regression population or incomplete tests')
        result = {'design': row['design'], 'track': row['track'],
                  'process_receipts': processes, 'test_log': binding(test_log)}
        if not row['completed']:
            require(not row['audited'] and row['process']['exit_status'] == 1,
                    'coverage failure mislabeled')
            require(row['design'] in ('s38584.1', 'tseng'), 'unclassified input failure')
            require('v1 importer does not silently omit root clock nets' in
                    (root / 'prepare.stderr.log').read_text(), 'input failure reason differs')
            require(not list(root.glob('process_*.process.json')), 'failed input launched host')
            result['status'] = 'unsupported_root_clock_zero_host_runs'
        else:
            require(row['audited'] and row['process']['exit_status'] == 0,
                    'successful execution lacks audit')
            publication_path = checked(row['publication_audit'])
            publication = json.loads(publication_path.read_text())
            require(publication['pass'] and
                    publication['auditor_sha256'] == sha(ROOT / 'tools/audit_development.py'),
                    'audit implementation changed')
            receipt_path = root / 'audit.json'
            require(sha(receipt_path) == publication['suite_audit_sha256'], 'suite receipt changed')
            receipt = json.loads(receipt_path.read_text())
            for relative, digest in receipt['artifacts'].items():
                require(sha(root / relative) == digest, 'changed audit input: ' + relative)
            for entry in receipt['sources']:
                require(sha(entry['snapshot']) == entry['sha256'], 'changed suite source archive')
            require(sha(root / 'build/fusionpar_host') == receipt['host_sha256'], 'host changed')
            for r in receipt['records']:
                require(r['process']['exit_status'] == 0, 'incomplete host run')
                require(r['charged_wall_ns'] == r['process']['wall_ns'] + r['common_conversion_ns'],
                        'conversion charge omitted or doubled')
                prepare = json.loads((root / 'prepare.process.json').read_text())
                require(r['common_conversion_ns'] == prepare['wall_ns'], 'wrong conversion charge')
                require(r['summary']['evaluations'] == r['summary']['commits'] + r['summary']['aborts'],
                        'candidate accounting mismatch')
                if row['track'] == 'equal_evaluation_feedback':
                    require(r['summary']['evaluations'] == 9, 'unequal evaluation budget')
            result.update(status='audit_inputs_unchanged', publication_audit=binding(publication_path),
                          archived_files_checked=len(receipt['artifacts']))
        rows.append(result)
        print(row['design'], row['track'], result['status'], flush=True)
    return {'schema': 'FUSIONPAR_FRAMEWORK_EVIDENCE_RECHECK_V1',
            'observed_utc': datetime.now(timezone.utc).isoformat(),
            'pass': True, 'summary': binding(summary_path), 'study': binding(study_path),
            'verifier': binding(Path(__file__)), 'counts': saved['counts'],
            'current_frozen_sources_checked': len(freeze['sources']), 'suites': rows,
            'limits': ['Evidence recheck, not new native P&R or timing measurement',
                       'Framework validity is limited to supported routed-design refinement',
                       'Four of six inputs supported; no universal fusion or FPGA speedup claim']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--summary', type=Path,
                   default=ROOT / 'experiments/independent_validation_status_2026-10-13.json')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        p.error('output already exists')
    result = recheck(args.summary.resolve())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['counts']), flush=True)
