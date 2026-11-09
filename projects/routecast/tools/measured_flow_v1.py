"""Execute a frozen sequential flow; record costs, never infer scientific gain."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def run(manifest, output):
    start = time.perf_counter()
    manifest = Path(manifest).resolve()
    output = Path(output).resolve()
    spec = json.loads(manifest.read_text())
    assert spec['schema'] == 'ROUTECAST_MEASURED_FLOW_V1'
    assert spec['stages'] and spec['bindings']
    names = [s['name'] for s in spec['stages']]
    assert len(names) == len(set(names))
    for s in spec['stages']:
        assert isinstance(s['argv'], list) and s['argv']
        assert all(isinstance(a, str) for a in s['argv'])
        assert Path(s['argv'][0]).is_absolute()
        assert s['argv'][0] in spec['bindings']
        assert Path(s['cwd']).is_absolute() and Path(s['cwd']).is_dir()
    output.mkdir(exist_ok=False)
    receipt = dict(schema='ROUTECAST_MEASURED_FLOW_RECEIPT_V1',
                   manifest=str(manifest), manifest_sha256=sha(manifest),
                   runner_sha256=sha(__file__), stages=[], status='running',
                   accepted_gain=False,
                   scope='Measured execution only; admission, quality, legality and matched controls require separate verification.')

    def save():
        receipt['elapsed_seconds'] = time.perf_counter() - start
        tmp = output / 'receipt.tmp'
        tmp.write_text(json.dumps(receipt, indent=2) + '\n')
        os.replace(tmp, output / 'receipt.json')

    save()
    try:
        assert all(sha(p) == h for p, h in spec['bindings'].items()), 'input binding mismatch'
        for i, s in enumerate(spec['stages']):
            tick = time.perf_counter()
            row = dict(name=s['name'], offset_seconds=tick-start,
                       status='running', argv=s['argv'], cwd=s['cwd'])
            receipt['stages'].append(row)
            save()
            with (output / f'{i:03d}.log').open('xb') as log:
                child = subprocess.Popen(s['argv'], cwd=s['cwd'], stdout=log,
                                         stderr=subprocess.STDOUT)
                row['pid'] = child.pid
                try:
                    row['startticks'] = Path(f'/proc/{child.pid}/stat').read_text().split(') ', 1)[1].split()[19]
                except FileNotFoundError:
                    row['startticks'] = None  # A very short command may already have exited.
                save()
                code = child.wait()
            row.update(exit_status=code, status='passed' if code == 0 else 'failed',
                       process_and_log_seconds=time.perf_counter()-tick)
            save()
            if code != 0:
                receipt['status'] = 'stage_failed_remaining_not_executed'
                break
        else:
            receipt['status'] = 'all_stages_exit_zero'
        assert all(sha(p) == h for p, h in spec['bindings'].items()), 'input mutated during flow'
    except Exception as error:
        receipt['status'] = 'execution_or_binding_error'
        receipt['error'] = f'{type(error).__name__}: {error}'
    receipt['unexecuted_stages'] = names[len(receipt['stages']):]
    receipt['terminal'] = True
    save()
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest')
    parser.add_argument('output')
    args = parser.parse_args()
    result = run(args.manifest, args.output)
    print(result['status'], flush=True)
    raise SystemExit(0 if result['status'] == 'all_stages_exit_zero' else 1)
