"""Verify actual candidate XO ABI/source and retained opcode stage modules."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import zipfile

R = Path(__file__).resolve().parents[1]
D = R / 'work/execute_opcode_split_hw_20261020'
B = R / 'work/insert_lookup_boundary_hw_20261020'


def main():
    refs = {}

    def sha(path):
        path = Path(path)
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                h.update(block)
        refs[str(path)] = h.hexdigest()
        return refs[str(path)]

    protocol = json.loads((D / 'protocol.json').read_text())
    for name, expected in protocol['source_sha256'].items():
        assert sha(name) == expected, name
    assert json.loads((D / 'manifest.json').read_text())['returncode'] == 0
    helper = R / 'tools/audit_insert_lookup_boundary_XO.py'
    spec = importlib.util.spec_from_file_location('xo_inspector', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parent, candidate = module.inspect(B / 'commit.xo'), module.inspect(D / 'commit.xo')
    for key in ['ports', 'args', 'control_protocol', 'version', 'device', 'target_ns', 'uncertainty_ns']:
        assert parent[key] == candidate[key], key
    assert len(candidate['ports']) == 8 and len(candidate['args']) == 29
    assert candidate['device'] == 'xcu280-fsvh2892-2L-e'
    source = D / 'source/net_commit_sharded_hbm.cpp'
    with zipfile.ZipFile(D / 'commit.xo') as archive:
        names = [n for n in archive.namelist() if n.endswith('/net_commit_sharded_hbm.cpp')]
        assert names and all(archive.read(n) == source.read_bytes() for n in names)
    solution = D / 'commit_temp/commit/dieroute_net_commit_sharded_hbm/dieroute_net_commit_sharded_hbm/solution'
    stages = []
    for name in ['phase_execute', 'phase_proposal_body', 'phase_ripup_body']:
        path = solution / 'syn/verilog' / ('dieroute_net_commit_sharded_hbm_p_anonymous_namespace_' + name + '.v')
        text = path.read_text()
        states = re.findall(r'parameter\s+ap_ST_fsm_state(\d+)\s*=\s*(\d+)\x27d', text)
        assert states, name
        stages.append({'function': name, 'states': len(states), 'one_hot_width': max(int(v[1]) for v in states)})
        sha(path)
    for path in [D / 'commit.xo', B / 'commit.xo', D / 'protocol.json', D / 'manifest.json', source, helper, Path(__file__).resolve()]:
        sha(path)
    report = {'status': 'actual_opcode_split_XO_ABI_source_and_three_stages_verified',
              'arguments': len(candidate['args']), 'ports': len(candidate['ports']), 'stages': stages,
              'HLS_resources': candidate['resources'], 'HLS_estimated_period_ns': candidate['estimated_ns'],
              'resource_delta_vs_parent': {k: candidate['resources'][k] - v for k, v in parent['resources'].items()},
              'source_sha256': refs, 'research_complete': False, 'adopted': False,
              'scope': 'Actual hardware compile, exact embedded source and unchanged external ABI; three separately synthesized opcode modules retained. No proof of routed register cuts, lower physical delay, final frequency, board execution or adoption.'}
    with (D / 'compiled_XO_review.json').open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: report[k] for k in ['status', 'arguments', 'ports', 'stages']}))


if __name__ == '__main__':
    main()
