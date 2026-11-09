"""Inventory named state correspondence; does not prove transition equivalence."""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'experiments/full_structural_native_register_mapping_v1_2026-10-09'
OUT.mkdir(exist_ok=True)
paths = [ROOT / 'experiments/full_ram_mapping_candidate_v1_2026-10-09/structural.json', ROOT / 'experiments/full_native_ram_gates_v3_2026-10-09/gates.json']
modules = []
for p in paths:
    modules.append(max(json.loads(p.read_text())['modules'].values(), key=lambda m: len(m.get('cells', {}))))
a, b = modules
aliases = collections.defaultdict(list)
for name, net in a['netnames'].items():
    if name not in b['netnames']:
        continue
    other = b['netnames'][name]
    if len(net['bits']) != len(other['bits']):
        continue
    for lane, (x, y) in enumerate(zip(net['bits'], other['bits'])):
        if isinstance(x, int):
            aliases[x].append((name, lane, y))
drivers = collections.defaultdict(list)
for name, cell in b['cells'].items():
    if cell['type'].startswith('$_DFF'):
        for bit in cell['connections']['Q']:
            drivers[bit].append({'cell': name, 'type': cell['type'], 'connections': cell['connections']})
all_outputs = collections.defaultdict(list)
for name, cell in b['cells'].items():
    for port, direction in cell['port_directions'].items():
        if direction == 'output':
            for bit in cell['connections'][port]:
                all_outputs[bit].append({'cell': name, 'type': cell['type'], 'port': port})
rows = []
for name, cell in a['cells'].items():
    if 'dff' not in cell['type'].lower():
        continue
    for lane, bit in enumerate(cell['connections']['Q']):
        matches = aliases[bit]
        candidates = sorted(set(x[2] for x in matches), key=str)
        state_candidates = [x for x in candidates if isinstance(x, int) and x in drivers]
        status = 'unique_native_state' if len(candidates) == 1 and len(state_candidates) == 1 else 'constant' if len(candidates) == 1 and isinstance(candidates[0], str) else 'unresolved'
        init = []
        for netname, netlane, target in matches:
            for side, mod in [('structural', a), ('native', b)]:
                value = mod['netnames'][netname].get('attributes', {}).get('init')
                if value is not None:
                    init.append({'side': side, 'alias': netname, 'lane': netlane, 'vector': value})
        rows.append({'cell': name, 'type': cell['type'], 'lane': lane, 'bit': bit, 'status': status, 'native_candidates': candidates, 'aliases': matches, 'native_drivers': [d for x in state_candidates for d in drivers[x]], 'candidate_output_drivers': [d for x in candidates for d in all_outputs[x]], 'structural_parameters': cell['parameters'], 'init_attributes': init})
target_counts = collections.Counter(r['native_candidates'][0] for r in rows if r['status'] == 'unique_native_state')
report = {'unique_native_state_targets': len(target_counts), 'shared_native_targets': sum(v > 1 for v in target_counts.values()), 'unresolved_output_driver_types': dict(collections.Counter(d['type'] for r in rows if r['status'] == 'unresolved' for d in r['candidate_output_drivers'])), 'inputs': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths], 'counts': dict(collections.Counter(r['status'] for r in rows)), 'total_structural_register_bits': len(rows), 'scope': 'Name-and-lane correspondence inventory only. No combinational cone equivalence, reset schedule equivalence, initial state coupling, ABC/export equivalence, or Full admission is established.', 'rows': rows}
(OUT / 'mapping_audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=2))
