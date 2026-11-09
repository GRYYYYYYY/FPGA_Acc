"""Guard completeness and failure-evidence checks in prospective evaluation."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_new_cohort import audit
from tileplace_vpr import ContractError, sha256


class NewCohortAuditTest(unittest.TestCase):
    def fixture(self, root):
        folder = root / 'case'
        folder.mkdir()
        stage = {'name': 'baseline', 'cwd': str(folder), 'command': ['native-vpr']}
        (folder / 'baseline.command.json').write_text(json.dumps(stage['command']))
        (folder / 'process.json').write_text(json.dumps({'returncode': 1, 'elapsed_s': 1}))
        (folder / 'stdout.log').write_text('failed baseline')
        (folder / 'stderr.log').write_text('architecture mismatch')
        protocol = {'files': [], 'output_root': str(root), 'scope': 'test',
                    'cases': [{'design': 'a', 'stages': [stage], 'refinements': []},
                              {'design': 'b', 'stages': [stage], 'refinements': []}]}
        path = root / 'protocol.json'
        path.write_text(json.dumps(protocol))
        matrix = {'protocol_sha256': sha256(path), 'cases': [{'design': 'a', 'status': 'fail',
                  'failed_stage': 'baseline', 'error': 'stage failed', 'stages': [], 'repeats': []}]}
        (root / 'progress.json').write_text(json.dumps(matrix))
        return path, matrix, folder

    def test_partial_failure_does_not_prove_full_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, matrix, _ = self.fixture(root)
            result = audit(path, sha256(path), partial=True)
            self.assertEqual((result['completed_cases'], result['expected_cases']), (1, 2))
            self.assertEqual(result['successful_cases'], 0)
            self.assertNotIn('successful_subset_geomean_change_pct', result)
            (root / 'summary.json').write_text(json.dumps(matrix))
            with self.assertRaises(ContractError):
                audit(path, sha256(path))

    def test_duplicate_case_and_missing_failure_logs_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, matrix, folder = self.fixture(root)
            matrix['cases'].append(matrix['cases'][0])
            (root / 'progress.json').write_text(json.dumps(matrix))
            with self.assertRaises(ContractError):
                audit(path, sha256(path), partial=True)
            matrix['cases'].pop()
            (root / 'progress.json').write_text(json.dumps(matrix))
            (folder / 'stderr.log').unlink()
            with self.assertRaises(FileNotFoundError):
                audit(path, sha256(path), partial=True)


if __name__ == '__main__':
    unittest.main()
