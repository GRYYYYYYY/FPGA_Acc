"""Frozen metrics plus independent Expat domain and histogram-rank checks."""
import math
from collections import Counter, defaultdict
from xml.parsers import expat

from prediction_metrics import compare
from stream_metric_domain_layered_v1 import metric_domain
from diagnose_neuron_complete_metric_hotspots_v1 import tie_diagnosis


def check_metric(prediction, truth, reported, k):
    assert prediction and set(prediction) == set(truth)
    ids = sorted(truth)
    k = min(k, len(ids))
    ranks = []
    for values in (prediction, truth):
        histogram = Counter(values.values())
        prior = 0
        rank = {}
        for value, count in sorted(histogram.items()):
            rank[value] = prior + (count - 1) / 2
            prior += count
        ranks.append(rank)
    mean = (len(ids) - 1) / 2
    a = [ranks[0][prediction[n]] - mean for n in ids]
    b = [ranks[1][truth[n]] - mean for n in ids]
    denominator = math.sqrt(sum(x*x for x in a) * sum(x*x for x in b))
    correlation = None if denominator == 0 else sum(x*y for x, y in zip(a, b)) / denominator
    if correlation is None:
        assert reported['spearman'] is None
    else:
        assert abs(reported['spearman'] - correlation) < 1e-12
    ps = sorted(ids, key=lambda n: (-prediction[n], n))[:k]
    ts = sorted(ids, key=lambda n: (-truth[n], n))[:k]
    hit = len(set(ps) & set(ts)) / k
    assert reported['precision_at_k'] == reported['recall_at_k'] == hit
    assert reported['k'] == k and reported['universe_size'] == len(ids)
    assert reported['nonzero_truth'] == sum(truth[n] > 0 for n in ids)
    assert abs(reported['mae'] - sum(abs(prediction[n] - truth[n]) for n in ids)/len(ids)) < 1e-12
    assert reported['truth_k_boundary'] == truth[ts[-1]]
    assert reported['prediction_k_boundary'] == prediction[ps[-1]]


def independent_domain(graph, prediction, truth):
    cp, ct = {}, {}
    capacity, pspan, tspan = defaultdict(int), defaultdict(int), defaultdict(int)
    counts = Counter()
    wanted = set(prediction) | set(truth)
    found = set()
    stack = []
    current = [None]

    class Finished(Exception):
        pass

    def start(tag, attrs):
        parent = stack[-1] if stack else None
        if tag == 'node' and parent == 'rr_nodes':
            current[0] = dict(attrs)
        if parent == 'node' and tag in ('loc', 'segment') and current[0] is not None:
            current[0][tag] = dict(attrs)
        stack.append(tag)

    def end(tag):
        parent = stack[-2] if len(stack) > 1 else None
        if tag == 'node' and parent == 'rr_nodes':
            node = current[0]
            nid, kind = node['id'], node['type']
            cap = int(node['capacity'])
            assert cap >= 0
            counts[kind] += 1
            if nid in wanted:
                found.add(nid)
            if kind in ('CHANX', 'CHANY') and cap > 0:
                assert nid not in cp, 'duplicate positive-capacity channel identity'
                pv, tv = prediction.get(nid, 0), truth.get(nid, 0)
                cp[nid], ct[nid] = pv/cap, tv/cap
                loc, segment = node['loc'], node['segment']['segment_id']
                for x in range(int(loc['xlow']), int(loc['xhigh']) + 1):
                    for y in range(int(loc['ylow']), int(loc['yhigh']) + 1):
                        key = f"{loc.get('layer', '0')},{x},{y},{kind},{segment}"
                        capacity[key] += cap
                        pspan[key] += pv
                        tspan[key] += tv
            current[0] = None
        assert stack.pop() == tag
        if tag == 'rr_nodes':
            raise Finished()

    parser = expat.ParserCreate()
    parser.StartElementHandler, parser.EndElementHandler = start, end
    complete = False
    with open(graph, 'rb') as stream:
        try:
            parser.ParseFile(stream)
        except Finished:
            complete = True
    assert complete and wanted <= found
    sp = {key: pspan[key]/cap for key, cap in capacity.items()}
    st = {key: tspan[key]/cap for key, cap in capacity.items()}
    return cp, ct, sp, st, dict(counts)


def evaluate_frame(graph, prediction, truth):
    for values in (prediction, truth):
        if any(not isinstance(n, str) or type(v) is not int or v < 0 for n, v in values.items()):
            raise ValueError('Expected string node IDs and nonnegative integer occupancies')
    p, t, sp, st, caps, counts = metric_domain(graph, prediction, truth)
    metrics = dict(concrete=compare(p, t, max(1, (len(t) + 19)//20)), spatial=compare(sp, st, 20))
    del p, t, sp, st, caps
    p, t, sp, st, independent_counts = independent_domain(graph, prediction, truth)
    assert independent_counts == counts
    for domain, pv, tv, k in (('concrete', p, t, max(1, (len(t) + 19)//20)), ('spatial', sp, st, 20)):
        check_metric(pv, tv, metrics[domain], k)
    ties = dict(concrete=tie_diagnosis(p, t, metrics['concrete']['k']),
                spatial=tie_diagnosis(sp, st, min(20, len(st))))
    return dict(metrics=metrics, ties=ties, original_node_counts=counts,
                independent_Expat_domain_and_histogram_metrics_pass=True)
