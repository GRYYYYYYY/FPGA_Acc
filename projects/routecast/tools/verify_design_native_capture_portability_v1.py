"""Exact captured-vector parity and pre-native rejection for explicit settings."""
import json
import subprocess
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(R / 'tools'), str(R / 'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from load_initial_connection_criticalities_v1 import load


def main():
    out = R / 'experiments/design_native_capture_portability_v1_2026-10-13'
    new = out / 'capture'
    old = R / 'experiments/xtea_retained_native_inputs_v1_2026-10-13'
    bindings = closure([Path(__file__), R / 'tools/capture_design_native_inputs_v1.py'])
    for directory in [old, new]:
        p = directory / 'criticality/verification.json'
        proof = json.loads(p.read_text())
        assert proof['nonignored_pin_keys_exactly_manifest'] and proof['all_values_and_pin_identities_equal_v1']
        assert all(sha(q) == h for q, h in proof['bindings'].items())
        bindings.update(proof['bindings'])
        bindings[str(p)] = sha(p)
    files = ['criticality_v1/criticality.tsv', 'criticality/criticality.tsv', 'indexed/indexed.tsv', 'criticality/initial_connection_criticalities.json']
    for name in files:
        assert (old / name).read_bytes() == (new / name).read_bytes(), name
        bindings[str(old / name)] = sha(old / name)
        bindings[str(new / name)] = sha(new / name)
    a, b = load(old / 'criticality'), load(new / 'criticality')
    assert len(a) == len(b) == 2450 and dict(a) == dict(b)
    settings = json.loads((out / 'settings.json').read_text())
    proof = R / 'experiments/xtea_retained_input_preflight_v1_2026-10-13/verification.json'
    manifest = proof.parent / 'xtea.queries'
    rejections = []
    for case in ['unbound_manifest', 'changed_architecture_binding', 'non_integer_width', 'unbound_sdc']:
        d = out / case
        d.mkdir()
        trial_settings = json.loads(json.dumps(settings))
        trial_manifest = manifest
        if case == 'unbound_manifest':
            trial_manifest = d / 'unbound.queries'
            trial_manifest.write_bytes(manifest.read_bytes())
        elif case == 'changed_architecture_binding':
            trial_settings['bindings'][settings['architecture']] = '0' * 64
        elif case == 'non_integer_width':
            trial_settings['channel_width'] = 128.0
        else:
            sdc = d / 'unbound.sdc'
            sdc.write_text('create_clock -period 10 clock\n')
            trial_settings['sdc'] = str(sdc)
        config = d / 'settings.json'
        config.write_text(json.dumps(trial_settings, indent=2) + '\n')
        target = d / 'native_output'
        command = [sys.executable, str(R / 'tools/capture_design_native_inputs_v1.py'), str(proof), str(trial_manifest), str(config), str(target)]
        with (d / 'rejection.log').open('x') as log:
            status = subprocess.call(command, cwd=R, stdout=log, stderr=subprocess.STDOUT)
        text = (d / 'rejection.log').read_text()
        assert status != 0 and 'AssertionError' in text and not target.exists()
        rejections.append(dict(case=case, exit_status=status, rejected_before_output_directory_and_native_stage=True))
    for path in out.rglob('*'):
        if path.is_file():
            bindings[str(path)] = sha(path)
    assert all(sha(p) == h for p, h in bindings.items())
    result = dict(bindings=bindings, exact_capture_files=files, all_three_raw_native_tables_and_2450_criticalities_byte_equal_original=True, loader_values_equal=True, rejection_cases=rejections, scope='Explicit-input capture preserves certified XTEA observations and rejects unbound/invalid manifests, architecture, SDC and width before launching a native stage. Actual non-default-SDC Titan capture remains pending; no claim of completed architecture transfer or heldout prediction.')
    with (out / 'verification.json').open('x') as f:
        f.write(json.dumps(result, indent=2) + '\n')
    print('CAPTURE PORTABILITY PASS', len(files), 'byte-identical files,', len(a), 'criticalities,', len(rejections), 'pre-native rejections', flush=True)


if __name__ == '__main__':
    main()
