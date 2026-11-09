"""Evaluate only frozen on/off selections with a symmetric native acceptance gate."""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools/native_resume_prototype'))
from pre_route_endpoints import sha, placements
from source_binding_v2 import closure
from stream_native_route_audit import audit
from audit_native_route import NET
from shared_compact_native_inventory_v1 import Inventory
from canonical_reload_ignored_no_timeout_v1 import canonical_reload, binary as reload_binary, identity


def main():
    start = time.perf_counter()
    source = R / 'experiments/xtea_placement_feedback_decisions_v1_2026-10-13'
    proof = source / 'verification.json'
    v = json.loads(proof.read_text())
    assert v['all_eight_candidate_models_and_physical_event_audits_pass'] and v['decisions_frozen_before_new_native_labels']
    assert all(sha(p) == h for p, h in v['bindings'].items())
    decision_path = source / 'decision.json'
    assert sha(decision_path) == v['decision_sha256']
    decision = json.loads(decision_path.read_text())
    candidates = {r['candidate_id']: r for r in decision['rows']}
    assert set(candidates) == set(range(9))
    key = lambda r: (r['hpwl'], r['candidate_id'])
    admitted = [r for r in candidates.values() if r['sketch_overflow'] <= candidates[0]['sketch_overflow']]
    assert decision['off_candidate'] == min(candidates.values(), key=key)['candidate_id']
    assert decision['on_candidate'] == min(admitted, key=key)['candidate_id']
    cohort = R / 'experiments/xtea_placement_feedback_cohort_v2_2026-10-13'
    policy = json.loads((cohort / 'protocol.json').read_text())
    assert sha(cohort / 'protocol.json') == decision['cohort_protocol_sha256']
    out = R / 'experiments/xtea_placement_feedback_native_v1_2026-10-13'
    out.mkdir()
    bindings = {**v['bindings'], str(proof): sha(proof), **closure([Path(__file__)])}
    build = R / 'build/native_candidate_retained_search_2026-10-06'
    binary = build / 'sequence_vpr'
    receipt = json.loads((build / 'receipt.json').read_text())
    assert sha(binary) == receipt['binary_sha256']
    bindings.update(receipt['source_sha256'])
    bindings.update(receipt['shared_inputs_sha256'])
    arch = R / 'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
    for p in [build / 'receipt.json', binary, reload_binary, identity, arch]:
        bindings[str(p)] = sha(p)
    order = list(dict.fromkeys([0, decision['off_candidate'], decision['on_candidate']]))
    protocol = dict(bindings=bindings, unique_selected_order=order, decisions_sha256=sha(decision_path), shared_native_settings=dict(seed=1, workers=1, channel_width=128, maximum_router_iterations=100), native_seed_import=False, acceptance=policy['placement_shell']['acceptance'], scope='Fresh native routing only for baseline and frozen unique selections. Identical acceptance gate; no alternative-candidate oracle selection. Two arms may share identical selected placement evidence. Timing diagnostic on experimental async architecture. Prepared-cohort component costs and reused prior-state costs remain explicit; no end-to-end acceleration claim.')
    assert all(sha(p) == h for p, h in bindings.items())
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    endpoints = {cid: json.loads(Path(candidates[cid]['endpoint']).read_text()) for cid in order}
    graph = Path(endpoints[0]['inputs']['graph']['path'])
    inventory = Inventory(graph)
    rows = []
    for cid in order:
        ep = endpoints[cid]
        assert ep['graph_sha256'] == endpoints[0]['graph_sha256']
        assert all(sha(spec['path']) == spec['sha256'] for spec in ep['inputs'].values())
        d = out / ('candidate_%02d' % cid)
        d.mkdir()
        for key_name, target in [('blif', 'design.blif'), ('net', 'design.net'), ('place', 'design.place')]:
            # Endpoints bind graph/net/place; BLIF is archived beside the packed netlist.
            p = Path(ep['inputs']['net']['path']).parent / target if key_name == 'blif' else Path(ep['inputs'][key_name]['path'])
            assert p.is_file()
            bindings[str(p)] = sha(p)
            shutil.copyfile(p, d / target)
        assert placements(d / 'design.place', sha(d / 'design.net')) == placements(ep['inputs']['place']['path'], sha(ep['inputs']['net']['path']))
        cmd = [str(binary), str(arch), 'design.blif', '--route', '--net_file', 'design.net', '--place_file', 'design.place', '--route_file', 'output.route', '--read_rr_graph', str(graph), '--route_chan_width', '128', '--num_workers', '1', '--seed', '1', '--max_router_iterations', '100', '--check_route', 'full']
        print('PLACEMENT NATIVE START', cid, flush=True)
        tick = time.perf_counter()
        with (d / 'native.log').open('x') as log:
            status = subprocess.call(cmd, cwd=d, env={k: val for k, val in os.environ.items() if not k.startswith('ROUTECAST_')}, stdout=log, stderr=subprocess.STDOUT)
        row = dict(candidate_id=cid, exit_status=status, native_process_seconds=time.perf_counter() - tick, status='NATIVE_OR_AUDIT_FAILED')
        (d / 'terminal.json').write_text(json.dumps(row) + '\n')
        try:
            assert status == 0
            text = (d / 'native.log').read_text()
            assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
            assert 'NET-aware seed imported' not in text
            row.update(wirelength=int(re.findall(r'Total wirelength:\s*(\d+)', text)[-1]), diagnostic_cpd_ns=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)', text)[-1]), iterations=int(re.search(r'Successfully routed after (\d+) routing iterations', text)[1]))
            tick = time.perf_counter()
            physical = audit(graph, d / 'output.route')
            names = {int(m[1]): m[2] for line in (d / 'output.route').read_text().splitlines() if (m := NET.match(line))}
            required_names = set(ep['net_names'].values())
            observed = Counter((names[q['net_id']], q['source'], q['sink']) for q in physical['connections'] if names[q['net_id']] in required_names)
            required = Counter((ep['net_names'][str(q['net_id'])], q['source'], q['sink']) for q in ep['connections'])
            assert observed == required and physical['overflow_units'] == 0
            (d / 'physical_audit.json').write_text(json.dumps(physical) + '\n')
            row['physical_audit_seconds'] = time.perf_counter() - tick
            candidate = dict(files={str(p): sha(p) for p in d.iterdir() if p.is_file()}, command=cmd, width=128, decision='R', cpd_ns=row['diagnostic_cpd_ns'])
            tick = time.perf_counter()
            canonical = canonical_reload(candidate, d, out / ('candidate_%02d_canonical' % cid), inventory)
            assert canonical['semantic_consistency_gate_pass']
            row.update(canonical=canonical, canonical_audit_seconds=time.perf_counter() - tick, status='FULL_PHYSICAL_AND_CANONICAL_PASS')
        except Exception as exc:
            row['error'] = repr(exc)
        rows.append(row)
        (out / 'rows.json').write_text(json.dumps(rows, indent=2) + '\n')
        print('PLACEMENT NATIVE', cid, row['status'], row.get('error', ''), flush=True)
    assert all(r['status'] == 'FULL_PHYSICAL_AND_CANONICAL_PASS' for r in rows)
    byid = {r['candidate_id']: r for r in rows}
    baseline = byid[0]
    arms = {}
    for arm in ['off', 'on']:
        cid = decision[arm + '_candidate']
        trial = byid[cid]
        accepted = cid != 0 and trial['wirelength'] < baseline['wirelength'] and trial['diagnostic_cpd_ns'] <= baseline['diagnostic_cpd_ns']
        final_id = cid if accepted else 0
        final = byid[final_id]
        arms[arm] = dict(proposed_candidate_id=cid, native_gate_accepted=accepted, final_candidate_id=final_id, final_wirelength=final['wirelength'], final_diagnostic_cpd_ns=final['diagnostic_cpd_ns'], final_route=str(out / ('candidate_%02d' % final_id) / 'output.route'), final_placement=str(out / ('candidate_%02d' % final_id) / 'design.place'))
    assert sha(decision_path) == v['decision_sha256'] and all(sha(p) == h for p, h in bindings.items())
    result = dict(arms=arms, baseline={k: baseline[k] for k in ['wirelength', 'diagnostic_cpd_ns', 'iterations', 'native_process_seconds']}, full_native_driver_seconds=time.perf_counter() - start, decision_driver_seconds=decision['full_decision_driver_seconds'], promote_as_end_to_end_acceleration=False, scope=protocol['scope'])
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    for p in out.rglob('*'):
        if p.is_file():
            bindings[str(p)] = sha(p)
    (out / 'verification.json').write_text(json.dumps(dict(bindings=bindings, all_selected_native_physical_and_canonical_pass=True, decisions_unchanged_after_native=True, symmetric_acceptance_and_baseline_retention_applied=True, result=result), indent=2) + '\n')
    print('PLACEMENT FEEDBACK RESULT', json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
