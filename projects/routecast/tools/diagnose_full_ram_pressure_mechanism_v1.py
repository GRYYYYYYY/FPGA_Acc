"""Predictor-only attribution; counterfactual costs are not rerouted outcomes."""
import json
from collections import Counter, defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from prepared_csr import read, TYPES

R = Path(__file__).resolve().parents[1]
E = R / 'experiments'
B = E / 'full_ram_length_switch_prediction_v1_2026-10-09'
D = E / 'full_ram_pressure_mechanism_v1_2026-10-09'
D.mkdir(exist_ok=False)
receipt = json.loads((B / 'receipt.json').read_text())
assert receipt['status'] == 'COMPLETE_AUDITED_PREDICTION'
for path, digest in {**receipt['bindings'], **receipt['files']}.items():
    assert sha(path) == digest
p = json.loads((B / 'prediction.json').read_text())
m, f = read(B / 'csr', p['physical_graph_sha256'])
rank = {n: i for i, n in enumerate(f['node_ids'])}
dest = dict(zip(f['edge_ids'], (f['node_ids'][i] for i in f['dest_ranks'])))
owners = defaultdict(set)
net_nodes = defaultdict(set)
for c in p['connections']:
    net_nodes[c['net_id']].update([c['source'], *(dest[e] for e in c['physical_edge_ids'])])
for net, nodes in net_nodes.items():
    for n in nodes:
        owners[n].add(net)
assert {str(n): len(v) for n, v in owners.items()} == p['node_occupancy']
def penalty(d, cap):
    assert cap > 0
    return (256 * max(0, d - cap + 1) + cap - 1) // cap
totals = Counter()
connections = Counter()
for c in p['connections']:
    own_reduction = channel_cost = ipin_cost = 0
    for edge in c['physical_edge_ids']:
        n = dest[edge]; i = rank[n]; cap = f['capacities'][i]
        assert cap > 0 and c['net_id'] in owners[n]
        d = len(owners[n])
        if f['types'][i] in (TYPES['CHANX'], TYPES['CHANY']):
            full = penalty(d, cap)
            without_own = penalty(d - 1, cap)
            channel_cost += full
            own_reduction += full - without_own
            totals['channel_edge_touches'] += 1
            totals['at_capacity_channel_touches'] += d == cap
            totals['over_capacity_channel_touches'] += d > cap
        elif f['types'][i] == TYPES['IPIN']:
            ipin_cost += penalty(d - 1, cap)
    totals['old_path_channel_penalty_sum'] += channel_cost
    totals['old_path_own_exclusion_reduction_sum'] += own_reduction
    totals['old_path_counterfactual_ipin_penalty_sum'] += ipin_cost
    connections['own_exclusion_changes_old_path_cost'] += own_reduction > 0
    connections['own_exclusion_leaves_zero_channel_penalty'] += channel_cost == own_reduction
    connections['ipin_penalty_changes_old_path_cost'] += ipin_cost > 0
report = dict(
    scope='All original 16819 paths, predictor-only ownership. Costs on old paths only; no new search, quality, causal attribution or incremental-equivalence claim.',
    connections=len(p['connections']), nets=len(net_nodes), totals=dict(totals), affected=dict(connections),
    next_protocol=dict(cohort='all 16819 connections', alpha=256,
        cases=['exclude queried net, channels only', 'exclude queried net, channels and IPIN'],
        background='same frozen original length-switch unique-net ledger',
        cost_rule='base + ceil(256*max(0,demand-minus-own-capacity+1)/capacity)',
        evaluation='all spatial metrics, all-type excess occupancy, complete path audit, preparation and search costs; no target reads during prediction'),
    bindings={str(x): sha(x) for x in [Path(__file__), B/'receipt.json', B/'prediction.json', B/'csr/manifest.json', R/'tools/prepared_csr.py']})
assert report['connections'] == 16819
(D / 'diagnosis.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
