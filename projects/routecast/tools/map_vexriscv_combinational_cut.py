"""Map a flattened combinational state cut; retain sequential records verbatim."""
import json
import shutil
import subprocess
import time
from pathlib import Path
from pre_route_endpoints import sha


def main():
    root = Path(__file__).resolve().parents[1]
    front = root / 'experiments/vexriscv_smallest_frontend_candidate_2026-10-06'
    receipt = json.loads((front / 'receipt.json').read_text())
    assert sha(front / 'protocol.json') == receipt['protocol_sha256']
    assert sha(front / 'design.json') == receipt['outputs']['design.json']
    tool = json.loads((root / 'experiments/prospective_family_candidates_2026-10-06/frontend_availability.json').read_text())
    yosys = Path(tool['yosys_path'])
    abc = yosys.parent.parent / 'abc/abc'
    assert sha(yosys) == tool['sha256']
    out = root / 'experiments/vexriscv_combinational_cut_mapping_2026-10-06'
    out.mkdir()
    shutil.copyfile(front / 'design.json', out / 'input.json')
    shutil.copyfile(__file__, out / 'source.py')
    protocol = {'input_json_sha256': sha(front / 'design.json'), 'yosys_sha256': sha(yosys),
                'abc_sha256': sha(abc), 'source_sha256': sha(__file__),
                'scope': 'flatten hierarchy; cut sequential state into combinational inputs/outputs; LUT6 mapping and cut CEC only, no changed reset semantics',
                'unseen_family_claim': False}
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    commands = []
    def run(stage, command):
        start = time.monotonic()
        with (out / (stage + '.log')).open('w') as log:
            r = subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        commands.append({'stage': stage, 'command': command, 'exit_code': r.returncode, 'wall_s': time.monotonic()-start})
        assert r.returncode == 0, stage
    run('flatten', [str(yosys), '-p', 'read_json input.json; flatten; check -assert; write_blif flat.blif'])
    lines = (out / 'flat.blif').read_text().splitlines()
    assert sum(line.startswith('.model ') for line in lines) == 1
    inputs = next(line.split()[1:] for line in lines if line.startswith('.inputs '))
    outputs = next(line.split()[1:] for line in lines if line.startswith('.outputs '))
    sequential = []
    retained = []
    for line in lines:
        if line.startswith('.latch '):
            parts = line.split()
            assert len(parts) == 6 and parts[3] == 're'
            outputs.append(parts[1]); inputs.append(parts[2]); sequential.append(line)
        elif line.startswith('.subckt '):
            parts = line.split()
            assert parts[1] in ('$_DFF_PP0_', '$_DFF_PP1_'), parts[1]
            pins = dict(token.split('=',1) for token in parts[2:])
            assert set(pins) == {'C','D','Q','R'}
            outputs.extend([pins['D'],pins['C'],pins['R']]); inputs.append(pins['Q']); sequential.append(line)
        elif not line.startswith(('.model ', '.inputs ', '.outputs ', '.end')):
            retained.append(line)
    inputs = list(dict.fromkeys(inputs)); outputs = list(dict.fromkeys(outputs))
    # Clock/reset are observable at the cut; overlapping input/output signals are legal BLIF.
    cut = '.model state_cut\n.inputs ' + ' '.join(inputs) + '\n.outputs ' + ' '.join(outputs) + '\n' + '\n'.join(retained) + '\n.end\n'
    (out / 'cut.blif').write_text(cut)
    (out / 'sequential_records.json').write_text(json.dumps(sequential,indent=2)+'\n')
    run('map', [str(abc), '-c', 'read_blif cut.blif; strash; if -K 6; write_blif mapped_cut.blif'])
    assert (out / 'mapped_cut.blif').exists(), 'ABC may return zero on failure; require output'
    run('cec', [str(abc), '-c', 'cec cut.blif mapped_cut.blif'])
    text = (out / 'cec.log').read_text()
    assert 'Networks are equivalent' in text, text
    assert sha(yosys) == protocol['yosys_sha256'] and sha(abc) == protocol['abc_sha256']
    result = {'protocol_sha256': sha(out / 'protocol.json'), 'commands': commands,
              'sequential_records': len(sequential), 'cut_inputs': len(inputs), 'cut_outputs':len(outputs),
              'cut_cec_equivalent':True, 'sequential_records_unchanged':True,
              'artifacts': {name:sha(out/name) for name in ('flat.blif','cut.blif','mapped_cut.blif','sequential_records.json','cec.log')},
              'vpr_ready':False, 'scope':protocol['scope'],
              'limitations':['cut CEC is not whole sequential HDL equivalence','async reset models still require architecture support','no reconstructed sequential netlist or routing yet']}
    (out / 'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__ == '__main__':
    main()
