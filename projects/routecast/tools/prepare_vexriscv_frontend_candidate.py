"""Frozen HDL synthesis candidate; retain async-reset semantics and report unsupported cells."""
import datetime
import json
import shutil
import subprocess
import time
from pathlib import Path
from pre_route_endpoints import sha


def main():
    root = Path(__file__).resolve().parents[1]
    candidates = root / 'experiments/prospective_family_candidates_2026-10-06'
    manifest = json.loads((candidates / 'manifest.json').read_text())
    assert sha(candidates / 'manifest.json') == json.loads((candidates / 'receipt.json').read_text())['manifest_sha256']
    row = next(r for r in manifest['records'] if r['archived_path'].endswith('/VexRiscvSmallest.v'))
    hdl = root / row['archived_path']
    assert sha(hdl) == row['sha256']
    tool = json.loads((candidates / 'frontend_availability.json').read_text())
    yosys = Path(tool['yosys_path'])
    assert sha(yosys) == tool['sha256']
    out = root / 'experiments/vexriscv_smallest_frontend_candidate_2026-10-06'
    out.mkdir()
    shutil.copyfile(hdl, out / 'design.v')
    script = 'read_verilog design.v\nhierarchy -check -top VexRiscvSmallest\nsynth -top VexRiscvSmallest -lut 6\ndffunmap\ncheck -assert\nstat\nwrite_json design.json\nwrite_blif design.blif\n'
    (out / 'synth.ys').write_text(script)
    shutil.copyfile(__file__, out / 'source.py')
    command = [str(yosys), '-s', 'synth.ys']
    protocol = {'manifest_sha256': sha(candidates / 'manifest.json'), 'input': row,
                'yosys': tool, 'script_sha256': sha(out / 'synth.ys'), 'source_sha256': sha(__file__),
                'command': command, 'cwd': str(out), 'timeout_s': 600,
                'frozen_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'selection': 'smallest named CPU variant for frontend readiness, not QoR selection; entire VexRiscv family remains one candidate group',
                'reset_policy': 'preserve asynchronous resets; do not use async2sync or silently discard unsupported flip-flops',
                'unseen_family_claim': False}
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    print(json.dumps({'stage': 'synthesis_started', 'protocol_sha256': sha(out / 'protocol.json')}), flush=True)
    start = time.monotonic()
    with (out / 'stdout.log').open('wb') as log:
        try:
            result = subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT, timeout=600)
            code, timeout = result.returncode, False
        except subprocess.TimeoutExpired:
            code, timeout = None, True
    types = {}
    if code == 0:
        design = json.loads((out / 'design.json').read_text())
        for module in design['modules'].values():
            for cell in module.get('cells', {}).values():
                types[cell['type']] = types.get(cell['type'], 0) + 1
    receipt = {'exit_code': code, 'timed_out': timeout, 'wall_s': time.monotonic() - start,
               'protocol_sha256': sha(out / 'protocol.json'), 'stdout_sha256': sha(out / 'stdout.log'),
               'cell_types': types, 'outputs': {name: sha(out / name) for name in ('design.json', 'design.blif') if (out / name).exists()},
               'inputs_unchanged': sha(hdl) == row['sha256'] and sha(yosys) == tool['sha256'],
               'vpr_readiness': 'requires explicit cell/model and reset compatibility audit',
               'scope': 'synthesis candidate only; not semantic equivalence proof, packed input, unseen-family test or routing result'}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)
    assert code == 0 and receipt['inputs_unchanged']


if __name__ == '__main__':
    main()
