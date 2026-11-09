"""Independent original XML exact delay deltas for bbox3's changed paths."""
import json
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

from pre_route_endpoints import sha
from selected_path_budgets import budgets
from streaming_prediction_audit import Edges


def run():
    base = Path('experiments')
    comparison = base / 'conv_layer_search_variant_comparison_2026-10-06'
    roots = [base / 'conv_layer_length_switch_prediction_v2_2026-10-06',
             base / 'conv_layer_length_switch_bbox3_prediction_2026-10-06']
    cr = json.loads((comparison / 'receipt.json').read_text())
    assert cr['report_sha256'] == sha(comparison / 'report.json')
    report = json.loads((comparison / 'report.json').read_text())
    assert all(sha(p) == h for p, h in report['inputs_sha256'].items())
    selected = set(report['bbox3_changed_connection_ids'])
    assert len(selected) == 146
    cohorts = []
    bindings = {str(comparison / name): sha(comparison / name) for name in ('report.json', 'receipt.json')}
    graph_info = None
    for root in roots:
        p = json.loads((root / 'protocol.json').read_text())
        r = json.loads((root / 'receipt.json').read_text())
        assert r['protocol_sha256'] == sha(root / 'protocol.json')
        assert r['prediction_sha256'] == sha(root / 'prediction.json')
        audit = Path(str(root) + '_physical_audit')
        ar = json.loads((audit / 'receipt.json').read_text())
        assert ar['prediction_receipt_sha256'] == sha(root / 'receipt.json')
        assert ar['protocol_sha256'] == sha(audit / 'protocol.json')
        assert ar['result']['all_physical_and_union_checks_passed']
        assert graph_info is None or graph_info == p['inputs']['graph']
        graph_info = p['inputs']['graph']
        cohorts.append([row for row in json.loads((root / 'prediction.json').read_text())['connections']
                        if row['connection_id'] in selected])
        assert len(cohorts[-1]) == 146
        bindings.update({str(root / name): sha(root / name) for name in ('protocol.json', 'receipt.json', 'prediction.json')})
        bindings[str(audit / 'receipt.json')] = sha(audit / 'receipt.json')
    old = {r['connection_id']: r for r in cohorts[0]}
    for r in cohorts[1]:
        assert all(r[k] == old[r['connection_id']][k] for k in ('net_id', 'source', 'sink'))
    out = base / 'conv_layer_bbox3_changed_path_delay_audit_2026-10-06'
    out.mkdir()
    (out / 'source').mkdir()
    names = [Path(__file__).name, 'selected_path_budgets.py', 'path_rc.py',
             'streaming_prediction_audit.py', 'pre_route_endpoints.py']
    sources = {n: sha(Path('tools') / n) for n in names}
    for n in names:
        shutil.copyfile(Path('tools') / n, out / 'source' / n)
    protocol = {'inputs_sha256': bindings, 'source_sha256': sources,
                'graph': graph_info, 'selected_connection_ids': sorted(selected),
                'model': 'exact serialized buffered zero-Cinternal path RC, SOURCE RC/2 included; independent XML, no CSR electrical cache or integer rounding',
                'scope': 'changed development predictor path delays only; not shared branch loading, native STA/CPD or accepted repair'}
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    wanted = {eid for rows in cohorts for r in rows for eid in r['physical_edge_ids']}
    records = {}
    count = 0
    start = time.monotonic()
    for phase in (0, 1):
        stack = []
        if phase:
            wanted_nodes = {r['source'] for rows in cohorts for r in rows} | {r['sink'] for rows in cohorts for r in rows}
            wanted_nodes.update(n for edge in records.values() for n in (edge.source, edge.sink))
            nodes = {}
            switches = {}
        for event, element in ET.iterparse(graph_info['path'], events=('start', 'end')):
            if event == 'start':
                stack.append(element)
                continue
            parent = stack[-2].tag if len(stack) > 1 else None
            if phase == 0 and (element.tag, parent) == ('edge', 'rr_edges'):
                if count in wanted:
                    records[count] = SimpleNamespace(source=int(element.get('src_node')),
                                                     sink=int(element.get('sink_node')),
                                                     switch_id=int(element.get('switch_id')))
                count += 1
            elif phase and (element.tag, parent) == ('node', 'rr_nodes') and int(element.get('id')) in wanted_nodes:
                timing = element.find('timing')
                assert timing is not None and 'R' in timing.attrib and 'C' in timing.attrib
                nodes[int(element.get('id'))] = SimpleNamespace(timing=tuple(timing.attrib.items()))
            elif phase and (element.tag, parent) == ('switch', 'switches'):
                sid = int(element.get('id'))
                assert sid not in switches
                switches[sid] = ET.tostring(element, encoding='unicode')
            if (element.tag, parent) in (('edge', 'rr_edges'), ('node', 'rr_nodes'), ('switch', 'switches'), ('segment', 'segments')):
                stack[-2].remove(element)
                element.clear()
            stack.pop()
        if phase == 0:
            assert set(records) == wanted
    assert set(nodes) == wanted_nodes
    graph = SimpleNamespace(nodes=nodes, edges=Edges(records, count), switches=switches)
    before, after = [budgets(graph, rows) for rows in cohorts]
    assert set(before) == set(after) == selected
    values = [{'connection_id': cid, 'before': [before[cid].numerator, before[cid].denominator],
               'after': [after[cid].numerator, after[cid].denominator],
               'within_original_exact_path_budget': after[cid] <= before[cid]}
              for cid in sorted(selected)]
    (out / 'delays.json').write_text(json.dumps(values, indent=2) + '\n')
    assert sha(graph_info['path']) == graph_info['sha256']
    assert all(sha(p) == h for p, h in bindings.items()) and all(sha(Path('tools') / n) == h for n, h in sources.items())
    receipt = {'connections': 146, 'equal_delay': sum(after[c] == before[c] for c in selected),
               'lower_delay': sum(after[c] < before[c] for c in selected),
               'higher_delay': sum(after[c] > before[c] for c in selected),
               'all_within_original_exact_path_budget': all(after[c] <= before[c] for c in selected),
               'protocol_sha256': sha(out / 'protocol.json'), 'delays_sha256': sha(out / 'delays.json'),
               'selected_nodes': len(nodes), 'selected_edges': len(records),
               'wall_s': time.monotonic() - start, 'repair_committed': False, 'scope': protocol['scope']}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    run()
