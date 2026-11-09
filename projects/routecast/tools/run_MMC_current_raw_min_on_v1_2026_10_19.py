"""Fixed three-case missing raw_min_on control, without native target routing."""
import json
import os
import sys
import time
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parent / 'native_resume_prototype')]
from pre_route_endpoints import sha
from versioned_digest_cache_v1 import Cache
from run_native_current_timing_feedback_v1_2026_10_19 import predict

R = Path(__file__).resolve().parents[1]


def save(p, value):
    with p.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def main():
    out = R / 'experiments/mmc_current_raw_min_on_v1_2026-10-19'
    out.mkdir(exist_ok=False)
    inputs = R / 'experiments/mmc_current_feedback_inputs_v1_2026-10-19'
    proof = inputs / 'verification.json'
    verified = json.loads(proof.read_text())
    assert verified['status'] == 'ALL3_COMBINED_CURRENT_TIMING_BASE_ENDPOINT_ADMISSION_AND_9_REJECTIONS_PASS'
    bindings = {str(proof): sha(proof), str(Path(__file__).resolve()): sha(__file__)}
    source = R / 'tools/run_native_fresh_timing_feedback_v1_2026_10_18.py'
    current = R / 'tools/run_native_current_timing_feedback_v1_2026_10_19.py'
    assert current.read_text() == source.read_text().replace('from load_design_routing_inputs_v3 import', 'from load_design_routing_inputs_v4 import', 1)
    bindings.update({str(p): sha(p) for p in [source, current]})
    save(out / 'protocol.json', dict(bindings=bindings, cases=['episode_01', 'episode_02', 'episode_03'],
         policy='Unchanged original V2 raw_min initialized state, two rounds, local endpoint-closure scheduling, current observed initialized criticality; same present/history/span, budgets and admission guards.',
         native_jobs=0, target_labels_read=False, failures_preserved=True,
         scope='Missing control production on exposed development layouts; full physical/event audits and cold scoring required. No parameter tuning or gain claim.'))
    save(out / 'owner.json', dict(pid=os.getpid(), started_unix=time.time()))
    rows = []
    cache = Cache()
    with cache.installed():
        assert all(sha(p) == h for p, h in verified['bindings'].items())
        for case in ['episode_01', 'episode_02', 'episode_03']:
            epdir = R / 'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19' / case
            endpoint = epdir / 'demand/endpoints.json'
            staged = epdir / 'staged_input_verification_v1.json'
            stage = json.loads(staged.read_text())
            assert all(sha(p) == h for p, h in stage['bindings'].items())
            initial_dir = R / 'experiments/mmc_prospective_swap_initializers_v1_2026-10-19' / case
            ip = initial_dir / 'initial_independent_verification_v1.json'
            iv = json.loads(ip.read_text())
            assert iv['status'] == 'pass' and iv['all115572V2budgets_matched']
            assert all(sha(p) == h for p, h in iv['bindings'].items())
            warm = out / case / 'warm'
            warm.mkdir(parents=True)
            for name in ['initial.json', 'floors.json', 'history.json']:
                p = initial_dir / 'raw_min' / name
                (warm / name).symlink_to(p)
            wb = dict(iv['bindings'])
            wb.update({str(ip): sha(ip), str(endpoint): sha(endpoint), str(staged): sha(staged)})
            wb.update({str(warm / n): sha(warm / n) for n in ['initial.json', 'floors.json', 'history.json']})
            save(warm / 'verification.json', dict(schema='NATIVE_ENDPOINT_ANCHORED_WARM_INPUT_V2', bindings=wb,
                 endpoint=str(endpoint), dirty_nets=stage['affected']['affected_net_ids'],
                 native_staged_state_independent_xml_pass=True, zero_initial_history=True,
                 native_anchored_budget_policy='NATIVE_ENDPOINT_ANCHORED_PROXY_V2',
                 all_old_per_design_minima_independently_recertified=False,
                 initializer_policy='raw_min', initial_independent_verification=str(ip)))
            print('RAW_MIN_ON_START', case, flush=True)
            start = time.perf_counter()
            result = predict(endpoint, out / case / 'model', inputs / case / 'base/verification.json',
                             R / 'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19' / case,
                             warm, 'local')
            rows.append(dict(case=case, result=result, seconds=time.perf_counter()-start))
            print('RAW_MIN_ON_COMPLETE', case, rows[-1], flush=True)
    save(out / 'receipt.json', dict(status='ALL3_RAW_MIN_ON_PRODUCED_INDEPENDENT_AUDITS_PENDING', rows=rows,
         bindings=bindings, native_jobs=0, quality_gate_pass=False))


if __name__ == '__main__':
    main()
