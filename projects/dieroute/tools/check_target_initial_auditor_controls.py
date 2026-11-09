"""Exercise the research auditor using temporary copies; preserve all evidence."""
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'work/initial_lookahead_target_aware_variant_20261018'
AUDITOR = ROOT / 'tools/audit_target_aware_initial_native.py'

def main():
    out = ROOT / 'work/target_initial_auditor_controls_20261018'
    out.mkdir(exist_ok=False)
    original = EVIDENCE / 'independent_audit.json'
    original_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    results = []
    def replace_csv(path, mutate):
        with path.open() as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        mutate(rows)
        assert path.is_symlink()
        path.unlink()
        with path.open('x') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
    for case in ['pristine', 'consistent_false_zero', 'consistent_suppressed_direct', 'missing_attempt']:
        with tempfile.TemporaryDirectory(prefix='dieroute-initial-auditor-') as temporary:
            copy = Path(temporary)
            for p in EVIDENCE.iterdir():
                if p.name != 'independent_audit.json':
                    (copy / p.name).symlink_to(p, target_is_directory=p.is_dir())
            if case in ['consistent_false_zero', 'consistent_suppressed_direct']:
                queries = list(csv.DictReader((copy / 'queries_0.csv').open()))
                if case == 'consistent_false_zero':
                    index = next(i for i, row in enumerate(queries) if math.isinf(float(row['exact_direct_delay'])))
                    exact, selected = '0', '0'
                else:
                    index = next(i for i, row in enumerate(queries) if float(row['exact_direct_delay']) == 0 and float(row['wire_min_delay']) > 0)
                    exact, selected = 'inf', queries[index]['wire_min_delay']
                # Mutate all repeats identically, bypassing a mere repeat hash check.
                for i in range(5):
                    replace_csv(copy / f'queries_{i}.csv', lambda rows: rows[index].update(exact_direct_delay=exact, selected_delay=selected))
                    replace_csv(copy / f'initial_timing_{i}.csv', lambda rows: rows[index].update(lookahead_delay_s=selected))
            elif case == 'missing_attempt':
                path = copy / 'native_queue.json'
                data = json.loads(path.read_text())
                data['attempts'].pop()
                path.unlink()
                path.write_text(json.dumps(data))
            runner = copy / 'run_auditor.py'
            runner.write_text('import importlib.util\nfrom pathlib import Path\n'
                              f's=importlib.util.spec_from_file_location("auditor",{str(AUDITOR)!r})\n'
                              'm=importlib.util.module_from_spec(s)\ns.loader.exec_module(m)\n'
                              f'm.HERE=Path({str(copy)!r})\nm.main()\n')
            with (out / f'{case}.log').open('x') as log:
                result = subprocess.run([sys.executable, str(runner)], cwd=ROOT,
                                        stdout=log, stderr=subprocess.STDOUT)
            assert (result.returncode == 0) == (case == 'pristine'), case
            results.append({'case': case, 'returncode': result.returncode,
                            'expected': 'accept' if case == 'pristine' else 'reject'})
    assert hashlib.sha256(original.read_bytes()).hexdigest() == original_hash
    files = [AUDITOR, Path(__file__).resolve(), original, *out.glob('*.log')]
    report = {'status': 'pristine_accepted_and_three_target_initial_mutation_controls_rejected',
              'controls': results, 'original_audit_unchanged': True,
              'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
              'scope': 'Temporary symlink views with copied mutated CSVs only. Consistent all-repeat false/suppressed direct candidates must fail independent exact-terminal oracle checks; missing attempt must fail denominator check. Not comprehensive fault coverage or new native execution.',
              'research_complete': False}
    with (out / 'audit.json').open('x') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps({'status': report['status'], 'controls': results}))

if __name__ == '__main__':
    main()
