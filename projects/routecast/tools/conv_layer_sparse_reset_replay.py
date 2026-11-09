"""Frozen real-graph sparse-reset parity and ABBA host microbenchmark."""
import collections
import json
import shutil
import subprocess
import time
from pathlib import Path

from pre_route_endpoints import sha
from prepared_csr import read


def run():
    base = Path('experiments')
    parent = base / 'conv_layer_length_switch_prediction_v2_2026-10-06'
    front = base / 'conv_layer_global_frontend_v2_2026-10-06'
    csr = base / 'conv_layer_length_switch_csr_2026-10-06/csr'
    pp = json.loads((parent / 'protocol.json').read_text())
    pr = json.loads((parent / 'receipt.json').read_text())
    fr = json.loads((front / 'receipt.json').read_text())
    assert pr['protocol_sha256'] == sha(parent / 'protocol.json')
    assert pr['journal_sha256'] == sha(parent / 'net_results.jsonl')
    assert fr['outputs']['endpoints.json'] == sha(front / 'endpoints.json')
    assert pp['frontend_receipt_sha256'] == sha(front / 'receipt.json')
    m, fields = read(csr, pp['inputs']['graph']['sha256'])
    assert sha(csr / 'manifest.json') == pp['csr_manifest_sha256']
    groups = collections.defaultdict(list)
    for row in json.loads((front / 'endpoints.json').read_text())['connections']:
        groups[row['net_id']].append(row)
    nets = sorted(groups)
    assert len(nets) == 12867
    selected = [nets[i * (len(nets) - 1) // 127] for i in range(128)]
    expected = {row['net_id']: row['result'] for row in
                map(json.loads, (parent / 'net_results.jsonl').read_text().splitlines())
                if row['net_id'] in selected}
    queries = []
    for net in selected:
        sources = {r['source'] for r in groups[net]}
        assert len(sources) == 1
        queries.append(' '.join(map(str, [next(iter(sources)), *sorted({r['sink'] for r in groups[net]})])))
    del fields
    out = base / 'conv_layer_sparse_reset_replay_2026-10-06'
    out.mkdir()
    binaries = {'A': parent / 'consumer', 'B': Path('build/routecast_csr_authenticated_sparse_reset')}
    assert sha(binaries['A']) == pp['binary_sha256']
    for key, path in binaries.items():
        shutil.copy2(path, out / ('consumer_' + key))
    paths = [parent / 'receipt.json', parent / 'protocol.json', parent / 'net_results.jsonl',
             front / 'receipt.json', front / 'endpoints.json', csr / 'manifest.json',
             base / 'host_sparse_reset_contract_2026-10-06/receipt.json']
    bindings = {str(p): sha(p) for p in paths}
    names = [Path(__file__).name, 'csr_consumer/authenticated_sparse_reset_main.cpp',
             'csr_consumer/authenticated_host_sparse_reset_search.hpp']
    sources = {n: sha(Path('tools') / n) for n in names}
    (out / 'source').mkdir()
    for n in names:
        shutil.copyfile(Path('tools') / n, out / 'source' / Path(n).name)
    protocol = {'inputs_sha256': bindings, 'source_sha256': sources,
                'binary_sha256': {key: sha(out / ('consumer_' + key)) for key in binaries},
                'graph': pp['inputs']['graph'], 'csr_manifest_sha256': sha(csr / 'manifest.json'),
                'selected_net_ids': selected, 'selection': '128 equally spaced indices over sorted 12867-net cohort, endpoints only',
                'order': list('ABBAABBA'), 'warmup': 'first selected query, excluded from timed 128-query phase',
                'scope': 'real-graph host microbenchmark and sampled exact archived paths/counters parity; graph startup recorded separately; concurrent development workloads; no full-cohort parity, native QoR, device or end-to-end speedup claim'}
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    measurements = []
    for index, key in enumerate(protocol['order']):
        start = time.monotonic()
        with (out / f'run_{index}_{key}_stderr.log').open('w') as err:
            process = subprocess.Popen([str((out / ('consumer_' + key)).resolve()), str(csr.resolve()), '--batch'],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, text=True)
            try:
                process.stdin.write(queries[0] + '\n')
                process.stdin.flush()
                line = process.stdout.readline()
                assert line and json.loads(line) == expected[selected[0]], 'warmup mismatch'
                setup_s = time.monotonic() - start
                phase = time.monotonic()
                records = []
                for net, text in zip(selected, queries):
                    process.stdin.write(text + '\n')
                    process.stdin.flush()
                    line = process.stdout.readline()
                    assert line, 'consumer terminated early'
                    result = json.loads(line)
                    assert result == expected[net], f'canonical parity mismatch net {net}'
                    records.append({'net_id': net, 'result': result})
                query_s = time.monotonic() - phase
                process.stdin.close()
                assert process.wait() == 0
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait()
        result_path = out / f'run_{index}_{key}_results.json'
        result_path.write_text(json.dumps(records) + '\n')
        record = {'variant': key, 'queries': 128, 'setup_and_warmup_s': setup_s,
                  'query_phase_s': query_s, 'results_sha256': sha(result_path)}
        measurements.append(record)
        (out / 'measurements.json').write_text(json.dumps(measurements, indent=2) + '\n')
        print(json.dumps(record), flush=True)
    assert all(sha(p) == h for p, h in bindings.items())
    assert all(sha(Path('tools') / n) == h for n, h in sources.items())
    receipt = {'protocol_sha256': sha(out / 'protocol.json'),
               'measurements_sha256': sha(out / 'measurements.json'),
               'runs': 8, 'queries_per_run': 128, 'all_archived_paths_and_counters_exact': True,
               'scope': protocol['scope']}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    run()
