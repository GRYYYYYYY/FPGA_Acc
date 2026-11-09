#!/usr/bin/env python3
"""Compare old/new RR state views on frozen serial and speculative workloads."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError('comparison requires assertions')
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('reference-host', 'candidate-host', 'legacy-audit', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--repeats', type=int, default=5)
    a = p.parse_args()
    assert a.repeats >= 2
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for path, name in ((a.reference_host, 'reference'), (a.candidate_host, 'candidate')):
        shutil.copy2(path, out/name)
    for name in ('compare_rr_state_views.py', 'run_native_case.py'):
        shutil.copy2(Path(__file__).with_name(name), out/name)
    legacy = json.loads(a.legacy_audit.read_text())
    inputs = {str(a.legacy_audit.resolve()): sha256(a.legacy_audit)}
    for entry in legacy['runs']:
        for prefix in entry['command'][1:3]:
            pp = Path(prefix).resolve()
            for path in pp.parent.glob(pp.name+'.*'):
                if path.is_file():
                    inputs[str(path)] = sha256(path)
    record = dict(schema='dieroute.rr_state_view_comparison.v1', status='running', inputs=inputs,
                  binary_sha256={name: sha256(out/name) for name in ('reference', 'candidate')},
                  started_ns=time.time_ns(), runs=[], comparisons=[], board_result=False)
    manifest = out/'manifest.json'

    def save():
        tmp = out/'manifest.tmp';tmp.write_text(json.dumps(record, indent=2)+'\n');tmp.replace(manifest)

    save()
    env = {k: v for k, v in os.environ.items() if not k.startswith(('DIEROUTE_', 'PERSISTROUTE_'))}
    env.update(legacy['environment'])
    suffixes = ('.paths.csv', '.route_trees.csv', '.iterations.csv', '.audit.csv', '.resources', '.costs', '.timing_iterations.csv', '.transactions.csv')

    def run(entry, host, mode, rep):
        prefix = out/(entry['case']+'_'+mode+'_'+host+'_'+str(rep))
        command = [str(out/host), *entry['command'][1:3], str(prefix), entry['command'][4]]
        run_env = dict(env, DIEROUTE_SPECULATIVE_WORKERS='0' if mode == 'serial' else '4',
                       DIEROUTE_SHADOW_SYNC_WINDOWS='3' if mode == 'sync3' else '1')
        info = dict(command=command, host=host, mode=mode, repeat=rep, case=entry['case'],
                    environment={k: v for k, v in run_env.items() if k.startswith(('DIEROUTE_', 'PERSISTROUTE_'))})
        record['runs'].append(info)
        with Path(str(prefix)+'.log').open('w') as log:
            proc = subprocess.Popen(command, env=run_env, stdout=log, stderr=subprocess.STDOUT)
            info['pid'] = proc.pid;save();info['returncode'] = proc.wait()
        assert info['returncode'] == 0
        info['hashes'] = {suffix: sha256(str(prefix)+suffix) for suffix in suffixes}
        summary = json.loads(Path(str(prefix)+'.json').read_text())
        assert summary['legal']
        info['non_wall_summary'] = {k: v for k, v in summary.items() if k != 'wall_ms'}
        save()
        return info

    try:
        # The existing three serial workload hashes are already frozen controls.
        for entry in legacy['runs']:
            result = run(entry, 'candidate', 'serial', 0)
            assert all(result['hashes'][k] == v for k, v in entry['hashes'].items())
            reference_summary = json.loads(Path(entry['command'][3]+'.json').read_text())
            assert result['non_wall_summary'] == {k: v for k, v in reference_summary.items() if k != 'wall_ms'}
            record['comparisons'].append(dict(case=entry['case'], mode='serial', frozen_hashes_and_counters_equal=True))
        entry, = [r for r in legacy['runs'] if r['case'] == 'diffeq']
        for mode in ('sync1', 'sync3'):
            reference = run(entry, 'reference', mode, 0)
            for rep in range(a.repeats):
                candidate = run(entry, 'candidate', mode, rep)
                assert candidate['hashes'] == reference['hashes'], 'path/tree/state/transaction difference'
                assert candidate['non_wall_summary'] == reference['non_wall_summary'], 'semantic counter difference'
            record['comparisons'].append(dict(case='diffeq', mode=mode, repeats=a.repeats,
                                             all_eight_artifacts_and_non_wall_counters_equal=True))
        for path, digest in inputs.items():
            assert sha256(path) == digest, path
        record.update(status='passed', inputs_unchanged=True)
    except Exception as exc:
        record.update(status='failed', error=repr(exc));raise
    finally:
        record['finished_ns'] = time.time_ns()
        record['artifacts'] = {str(f.relative_to(out)): sha256(f) for f in out.iterdir() if f.is_file() and f != manifest}
        save()
    print(json.dumps(record['comparisons']))


if __name__ == '__main__':
    main()
