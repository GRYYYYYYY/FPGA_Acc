"""Bind unchanged graph costs to current endpoints; exercise combined admission."""
import json
import sys
import time
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parent / 'native_resume_prototype')]
from pre_route_endpoints import sha
from versioned_digest_cache_v1 import Cache
from load_design_routing_inputs_v4 import load

R = Path(__file__).resolve().parents[1]


def main():
    out = R / 'experiments/mmc_current_feedback_inputs_v1_2026-10-19'
    out.mkdir(exist_ok=False)
    original = R / 'experiments/mmc_native_node_base_mapping_v1_2026-10-10/verification.json'
    base = json.loads(original.read_text())
    rows, rejections, bindings = [], [], {}
    start = time.perf_counter()
    cache = Cache()
    with cache.installed():
        assert all(sha(p) == h for p, h in base['bindings'].items())
        for i in range(1, 4):
            case = f'episode_{i:02d}'
            ep = R / 'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19' / case / 'demand/endpoints.json'
            timing = R / 'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19' / case
            endpoint = json.loads(ep.read_text())
            graph = endpoint['inputs']['graph']
            assert base['bindings'].get(graph['path']) == graph['sha256'] == sha(graph['path'])
            dest = out / case / 'base'
            dest.mkdir(parents=True)
            payload = dest / 'node_base.u64'
            payload.write_bytes((original.parent / payload.name).read_bytes())
            proof = json.loads(json.dumps(base))
            proof['bindings'].update({str(original): sha(original), str(ep): sha(ep), str(payload): sha(payload)})
            pp = dest / 'verification.json'
            pp.write_text(json.dumps(proof, indent=2) + '\n')
            costs, values, admitted = load(ep, pp, timing, base['nodes'], base['scale'])
            assert len(costs) == 904438 and len(values) == 115572
            bindings.update(admitted)
            for fault, other, n, scale in [
                ('wrong_scale', timing, base['nodes'], base['scale'] + 1),
                ('wrong_node_domain', timing, base['nodes'] - 1, base['scale']),
                ('wrong_epoch_endpoint', timing.parent / f'episode_{i % 3 + 1:02d}', base['nodes'], base['scale']),
            ]:
                try:
                    load(ep, pp, other, n, scale)
                except ValueError as e:
                    rejections.append(dict(case=case, fault=fault, error=str(e)))
                else:
                    raise AssertionError('invalid combined input accepted: ' + fault)
            rows.append(dict(case=case, nodes=len(costs), connections=len(values), graph_bound_to_original_base=True))
            print('COMBINED_INPUT_PASS', case, flush=True)
        for name in ['load_design_routing_inputs_v4.py', 'load_explicit_timing_epoch_v3.py', 'load_initial_connection_criticalities_v3.py']:
            p = R / 'tools' / name
            bindings[str(p)] = sha(p)
        bindings[str(Path(__file__).resolve())] = sha(__file__)
        assert all(sha(p) == h for p, h in bindings.items())
    (out / 'verification.json').write_text(json.dumps(dict(
        status='ALL3_COMBINED_CURRENT_TIMING_BASE_ENDPOINT_ADMISSION_AND_9_REJECTIONS_PASS',
        rows=rows, rejections=rejections, bindings=bindings,
        seconds=time.perf_counter() - start,
        scope='Same-graph original audited node-base payload transfer and current timing admission. No new node getter equivalence, route legality, feedback execution or quality gain.'
    ), indent=2) + '\n')


if __name__ == '__main__':
    main()
