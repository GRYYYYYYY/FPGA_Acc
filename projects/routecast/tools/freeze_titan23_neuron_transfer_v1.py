"""Freeze original Titan23 neuron inputs and current method before transfer runs."""
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as E
from collections import Counter

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure


def main():
    out = R / 'experiments/titan23_neuron_transfer_freeze_v1_2026-10-13'
    out.mkdir()
    origin = R.parent / 'tileplace/experiments/titan23_stereo_vision_input_capture_2026-09-02.json'
    captured = json.loads(origin.read_text())['official_archive']
    archive = Path(captured['path'])
    assert archive.stat().st_size == captured['size_bytes'] and sha(archive) == captured['sha256']
    vtr = R.parent / 'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
    architecture = vtr / 'vtr_flow/arch/titan/stratixiv_arch.timing.xml'
    names = {'neuron_stratixiv_arch_timing.blif': 'design.blif', 'neuron_stratixiv_arch_timing.sdc': 'design.sdc'}
    members, copied = [], {}
    print('ARCHIVE AUTHENTICATED; extracting original mapped input/SDC', flush=True)
    with tarfile.open(archive, 'r|gz') as stream:
        for member in stream:
            path = Path(member.name)
            if not member.isfile() or '/titan23/stratixiv/' not in '/' + member.name:
                continue
            if path.suffix in ['.blif', '.sdc']:
                members.append(dict(name=member.name, size=member.size))
            if path.name not in names:
                continue
            assert path.name not in copied
            target = out / names[path.name]
            with stream.extractfile(member) as source, target.open('xb') as sink:
                shutil.copyfileobj(source, sink, length=1048576)
            assert target.stat().st_size == member.size
            copied[path.name] = dict(member=member.name, archive_sha256=captured['sha256'], path=str(target), sha256=sha(target))
    assert set(copied) == set(names)
    for name in names:
        local = vtr / 'vtr_flow/benchmarks/titan_blif/titan23/stratixiv' / name
        assert sha(local) == copied[name]['sha256']
    shutil.copyfile(architecture, out / 'architecture.xml')
    assert sha(out / 'architecture.xml') == sha(architecture)
    print('ORIGINAL INPUTS MATCH; checking architecture and recorded exposure', flush=True)
    used = Counter()
    for line in (out / 'design.blif').open():
        if line.startswith('.subckt '):
            used[line.split()[1]] += 1
    root = E.parse(out / 'architecture.xml').getroot()
    models = {m.get('name') for m in root.find('models')}
    assert set(used) <= models
    switches = Counter(s.get('type') for s in root.find('switchlist'))
    assert set(switches) <= {'buffer', 'mux', 'tristate'}
    # Name/hash evidence is recorded; absence is not promoted to a genealogy proof.
    patterns = ['neuron_stratixiv_arch_timing', copied['neuron_stratixiv_arch_timing.blif']['sha256']]
    cmd = ['rg', '-l', '-F']
    for pattern in patterns:
        cmd += ['-e', pattern]
    cmd += ['-g', 'protocol.json', '-g', '*inventory*.json', '-g', '*readiness*.json', '-g', '*.py', '-g', '*.md', 'experiments', 'tools', 'README.md', 'RESEARCH_PLAN.md']
    searched = subprocess.run(cmd, cwd=R, capture_output=True, text=True)
    assert searched.returncode in [0, 1]
    matches = [p for p in searched.stdout.splitlines() if Path(p).resolve() != Path(__file__).resolve() and not (R / p).resolve().is_relative_to(out)]
    dependencies = [R / 'tools' / n for n in ['run_design_scoped_cached_retained_tree_v1.py', 'run_design_scoped_full_search_control_v1.py', 'run_warm_epoch_retained_update_v1.py', 'verify_warm_epoch_retained_update_v1.py', 'verify_resident_demand_frame_direct_lattice_v7.py', 'prediction_metrics.py', 'pre_route_endpoints.py']]
    bindings = {**closure([Path(__file__), *dependencies]), str(origin): sha(origin), str(archive): sha(archive), str(architecture): sha(architecture)}
    build = R / 'build/native_candidate_retained_search_2026-10-06'
    receipt = json.loads((build / 'receipt.json').read_text())
    assert sha(build / 'sequence_vpr') == receipt['binary_sha256']
    bindings.update(receipt['source_sha256'])
    bindings.update(receipt['shared_inputs_sha256'])
    for p in [build / 'receipt.json', build / 'sequence_vpr', out / 'design.blif', out / 'design.sdc', out / 'architecture.xml']:
        bindings[str(p)] = sha(p)
    for p in matches:
        bindings[str((R / p).resolve())] = sha(R / p)
    protocol = dict(
        frozen_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), bindings=bindings,
        benchmark='Titan23/neuron', selected_reason='Only Titan23 mapped circuit directly present in the local VTR benchmark directory; size and original architecture checked before any new RouteCast outcome. This is a transfer admission case, not a representative or best-performing subset of Titan23.',
        provenance=dict(official_archive_record=captured, members=copied, matches_existing_vtr_inputs=True, original_default_architecture=str(architecture), special_neuron_architecture_used=False, local_git_warning='git rev-parse in the vendor directory resolves to the FPGA_Acc parent repository, so the directory suffix is not an authenticated VTR commit.'),
        available_titan23_stratixiv_members=members,
        static_architecture_admission=dict(subcircuit_counts=dict(used), all_subcircuit_models_declared=True, switch_type_counts=dict(switches), rr_graph_capacity_and_electrical_semantics_pending=True),
        exposure=dict(search_command=cmd, local_metadata_matches=matches, scope='Direct benchmark-name/content-hash references in local protocol/inventory/readiness/source/docs only. No route or QoR labels consumed. Indirect design-family genealogy and external exposure are not established.', strict_unseen_family_certified=False),
        method=dict(criticality='Original native initialized per-pin criticality, explicit epoch; retain across a placement move only with exact stable-pin remap.', node_base='Original native initialized cost-index observation with XML/float32 independent reconstruction.', budget='max(1ns,ceil(1.5*zero-price exact buffered-RC floor))', rounds=2, retention='fanout>=16, keep globally uncongested old branches before owner release; same guarded wholeNET fallback', controls=['full-search same numerical objective/schedule', 'cold native same frozen placement', 'geometry on same full resource universe'], local_update='Exact endpoint wholeNET/sharedSOURCE closure; history/epochs inherited; compare all/local schedules without assuming global reoptimization equivalence.', cost='Record all input/graph preparation, model, audit and final native phases; reused work explicitly separated. No omitted cost may support net speedup.'),
        native=dict(binary=str(build / 'sequence_vpr'), seed=1, workers=1, channel_width=300, maximum_router_iterations=100, sdc=str(out / 'design.sdc'), preserve_original_timing_constraints=True),
        execution_order=['native pack', 'native place using original architecture and SDC', 'RR-only export with expected missing-route stop', 'physical endpoint/ignored identity/criticality/node-base admission', 'frozen model and independent physical/event audits', 'native reference and metrics', 'placement perturbation on/off after separate frozen candidate protocol'],
        failure_policy='Keep original failure and input; no architecture edits, subcircuit deletion, timeout censoring, candidate substitution or parameter retuning to obtain an admissible case.',
        scope='Original Titan mapped benchmark and SDC transfer; no original-HDL equivalence, achieved family holdout, full Titan23 coverage, final QoR or hardware claim.',
    )
    assert all(sha(p) == h for p, h in bindings.items())
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    (out / 'verification.json').write_text(json.dumps(dict(bindings={**bindings, str(out / 'protocol.json'): sha(out / 'protocol.json')}, archive_members_and_local_inputs_byte_identical=True, all_declared_models_and_buffered_architecture_switches_pass=True, native_jobs_started=False, local_reference_matches=matches, strict_unseen_family_certified=False), indent=2) + '\n')
    print('TITAN NEURON FROZEN', len(used), 'subcircuit models', len(matches), 'previous metadata matches', flush=True)


if __name__ == '__main__':
    main()
