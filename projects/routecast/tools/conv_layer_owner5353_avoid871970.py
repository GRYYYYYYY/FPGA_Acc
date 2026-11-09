"""Development joint reservation search over a frozen five-net ownership closure.

Fix the audited target tree, then try deterministic greedy owner-net orders.
Failure does not prove the absence of alternative trees or joint assignments.
"""
import collections
import itertools
import json
import shutil
import time
from array import array
from fractions import Fraction
from pathlib import Path

from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from csr_min_delay_feasibility import query
from pre_route_endpoints import sha
from prepared_csr import U64, read


def run():
    base = Path('experiments')
    parent = base / 'conv_layer_length_switch_prediction_v2_2026-10-06'
    selection = base / 'conv_layer_shared_tree_owner_closure_2026-10-06/report.json'
    budget = base / 'conv_layer_shared_tree_owner_closure_exact_budgets_2026-10-06'
    target = base / 'conv_layer_shared_tree_avoidance_2026-10-06'
    context = base / 'conv_layer_exact_buffered_rc_classes_2026-10-06'
    br = json.loads((budget / 'receipt.json').read_text())
    bp = json.loads((budget / 'protocol.json').read_text())
    assert br['protocol_sha256'] == sha(budget / 'protocol.json')
    assert br['budgets_sha256'] == sha(budget / 'budgets.json')
    assert all(sha(p) == h for p, h in bp['selection_sha256'].items())
    pp = json.loads((parent / 'protocol.json').read_text())
    pr = json.loads((parent / 'receipt.json').read_text())
    pick = json.loads(selection.read_text())
    assert pr['protocol_sha256'] == sha(parent / 'protocol.json')
    assert sha(parent / 'prediction.json') == pr['prediction_sha256'] == pick['prediction_sha256']
    tp = json.loads((target / 'protocol.json').read_text())
    tr = json.loads((target / 'receipt.json').read_text())
    assert tr['protocol_sha256'] == sha(target / 'protocol.json') and tr['journal_sha256'] == sha(target / 'queries.jsonl')
    assert all(sha(p) == h for p, h in tp['inputs_sha256'].items())
    target_audit = base / 'conv_layer_shared_tree_candidate_xml_audit_2026-10-06'
    target_budget = base / 'conv_layer_shared_tree_candidate_xml_budget_audit_2026-10-06'
    ta = json.loads((target_audit / 'receipt.json').read_text())
    tap = json.loads((target_audit / 'protocol.json').read_text())
    tb = json.loads((target_budget / 'receipt.json').read_text())
    tbp = json.loads((target_budget / 'protocol.json').read_text())
    assert ta['protocol_sha256'] == sha(target_audit / 'protocol.json')
    assert tap['parent_receipt_sha256'] == sha(target / 'receipt.json')
    assert ta['result']['all_physical_and_union_checks_passed']
    assert tb['protocol_sha256'] == sha(target_budget / 'protocol.json')
    assert tb['all_candidates_within_original_exact_path_budget']
    assert tbp['physical_receipt_sha256'] == sha(target_audit / 'receipt.json')
    assert tb['budgets_sha256'] == sha(target_budget / 'budgets.json')
    graph = pp['inputs']['graph']
    assert tp['graph'] == graph and sha(graph['path']) == graph['sha256']
    m, f = read(base / 'conv_layer_length_switch_csr_2026-10-06/csr', graph['sha256'])
    assert sha(base / 'conv_layer_length_switch_csr_2026-10-06/csr/manifest.json') == pp['csr_manifest_sha256']
    rc = ExactBufferedRC(f, *load(context, graph['sha256']))
    slots = array('Q', [0]) * m['edges']
    for slot, eid in enumerate(f['edge_ids']):
        slots[eid] = slot

    def used(source, sink, edges):
        nodes = {source}
        current = source
        for eid in edges:
            slot = slots[eid]
            assert f['row_offsets'][current] <= slot < f['row_offsets'][current + 1]
            current = f['dest_ranks'][slot]
            assert current not in nodes
            nodes.add(current)
        assert current == sink
        return nodes

    def span(nodes):
        return sum(max(f['xhigh'][n] - f['xlow'][n], f['yhigh'][n] - f['ylow'][n]) + 1
                   for n in nodes if f['types'][n] in (4, 5))

    pred = json.loads((parent / 'prediction.json').read_text())
    rows = [r for r in pred['connections'] if r['net_id'] in pick['affected_net_ids']]
    assert len(rows) == 7 and {r['connection_id'] for r in rows} == set(pick['whole_net_connection_ids'])
    budgets = {r['connection_id']: Fraction(r['delay_seconds_numerator'], r['delay_seconds_denominator'])
               for r in json.loads((budget / 'budgets.json').read_text())}
    assert set(budgets) == {r['connection_id'] for r in rows}
    grouped = collections.defaultdict(list)
    old = collections.defaultdict(set)
    for row in rows:
        grouped[row['net_id']].append(row)
        old[row['net_id']].update(used(row['source'], row['sink'], row['physical_edge_ids']))
        assert rc.path(row['source'], row['sink'], row['physical_edge_ids']) == budgets[row['connection_id']]
    before = collections.Counter({int(n): v for n, v in pred['node_occupancy'].items()})
    background = before.copy()
    for nodes in old.values():
        background.subtract(nodes)
    assert all(v >= 0 for v in background.values())
    target_rows = [r for r in map(json.loads, (target / 'queries.jsonl').read_text().splitlines()) if r['net_id'] == 5376]
    fixed = []
    fixed_nodes = set()
    for row in target_rows:
        assert row['result']['status'] == 'FOUND'
        edges = row['result']['physical_edge_ids']
        assert rc.path(row['source'], row['sink'], edges) <= budgets[row['connection_id']]
        fixed.append({k: row[k] for k in ('connection_id', 'net_id', 'source', 'sink')} | {'physical_edge_ids': edges})
        fixed_nodes.update(used(row['source'], row['sink'], edges))
    assert len(fixed) == 2 and span(fixed_nodes) == 50 < span(old[5376])
    initial = background.copy()
    initial.update(fixed_nodes)
    assert all(v <= max(f['capacities'][n], before[n]) for n, v in initial.items())
    out = base / 'conv_layer_owner5353_avoid871970_feasibility_2026-10-06'
    out.mkdir()
    (out / 'source').mkdir()
    names = [Path(__file__).name, 'prepared_csr.py', 'pre_route_endpoints.py',
             'buffered_rc_context.py', 'buffered_rc_node_classes.py',
             'csr_exact_buffered_rc.py', 'csr_min_delay_feasibility.py']
    sources = {n: sha(Path('tools') / n) for n in names}
    for n in names:
        shutil.copyfile(Path('tools') / n, out / 'source' / n)
    paths = [selection, parent / 'prediction.json', parent / 'receipt.json', budget / 'receipt.json',
             budget / 'budgets.json', target / 'protocol.json', target / 'receipt.json', target / 'queries.jsonl',
             context / 'receipt.json', target_audit / 'receipt.json', target_budget / 'receipt.json']
    bindings = {str(p): sha(p) for p in paths}
    protocol = {'inputs_sha256': bindings, 'source_sha256': sources, 'graph': graph,
                'node_limit': m['nodes'],
                'policy': 'only original net5353 CID9812; original actual pins/exact budget; forbid node871970; all other net occupancy optimistically relaxed; no span objective or shared-tree restriction',
                'scope': 'single fixed-pin original-budget resource-avoidance feasibility; UNREACHABLE with full-node cap establishes policy-specific forced node; not free-pin or native STA claim'}
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    statuses = collections.Counter()
    start = time.monotonic()
    with (out / 'queries.jsonl').open('w') as journal:
        for row in sorted((r for r in rows if r['net_id'] == 5353), key=lambda r: r['connection_id']):
            source, sink = row['source'], row['sink']
            opin = f['dest_ranks'][slots[row['physical_edge_ids'][0]]]
            ipin = f['dest_ranks'][slots[row['physical_edge_ids'][-2]]]
            def allowed(node, slot):
                dest = f['dest_ranks'][slot]; kind = f['types'][dest]
                if f['costs'][slot] == U64 or not f['capacities'][dest]:
                    return False
                if dest == 871970:
                    return False
                if node == source:
                    return dest == opin
                if kind in (4, 5):
                    return f['types'][node] in (2, 4, 5)
                if kind == 3:
                    return dest == ipin and f['types'][node] in (2, 4, 5)
                return kind == 1 and dest == sink and node == ipin
            if source == 871970:
                result = {'status': 'SOURCE_CAPACITY_BLOCKED'}
            else:
                result = query(rc, source, sink, budgets[row['connection_id']], allowed, max_labels=m['nodes'])
            if isinstance(result.get('delay'), Fraction):
                result['delay'] = [result['delay'].numerator, result['delay'].denominator]
            record = {k: row[k] for k in ('connection_id', 'net_id', 'source', 'sink')}
            record.update(original_opin=opin, original_ipin=ipin, result=result)
            journal.write(json.dumps(record) + '\n'); journal.flush()
            statuses[result['status']] += 1
            print(json.dumps({'connection_id': row['connection_id'], 'net_id': row['net_id'], 'status': result['status']}), flush=True)
    assert all(sha(p) == h for p, h in bindings.items()) and all(sha(Path('tools') / n) == h for n, h in sources.items())
    receipt = {'queries': 1, 'statuses': dict(statuses), 'wall_s': time.monotonic()-start,
               'protocol_sha256': sha(out/'protocol.json'), 'journal_sha256': sha(out/'queries.jsonl'),
               'repair_committed': False, 'scope': protocol['scope']}
    assert sum(statuses.values()) == 1
    (out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    run()
