"""Add missing cold raw_min_on control without changing archived candidate scores."""
import json
import pathlib
import xml.etree.ElementTree as ET
from collections import Counter
from fractions import Fraction
from pre_route_endpoints import sha
from prediction_metrics import compare

R = pathlib.Path(__file__).resolve().parents[1]


def main():
    source = R / 'experiments/mmc_current_raw_min_on_v1_2026-10-19'
    prior = R / 'experiments/mmc_complete_static_criticality_cold_quality_v1_2026-10-19'
    out = R / 'experiments/mmc_current_raw_min_on_cold_control_v1_2026-10-19'
    out.mkdir(exist_ok=False)
    result_path = prior / 'results.json'
    results = json.loads(result_path.read_text())
    metric_proof = prior / 'independent_metric_verification_v1.json'
    pv = json.loads(metric_proof.read_text())
    assert pv['status'] == 'ALL3_33_COLD_METRIC_VECTORS_MAE_AND_FROZEN_DECISIONS_INDEPENDENTLY_VERIFIED'
    assert pv['bindings'][str(result_path)] == sha(result_path)
    bindings = {str(p): sha(p) for p in [result_path, metric_proof, pathlib.Path(__file__).resolve(), R/'tools/prediction_metrics.py']}
    ep = R / 'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/episode_01/demand/endpoints.json'
    graph = pathlib.Path(json.loads(ep.read_text())['inputs']['graph']['path'])
    channels, bins, stack = [], {}, []
    for event, node in ET.iterparse(graph, events=('start', 'end')):
        if event == 'start':
            stack.append(node)
            continue
        if node.tag == 'node' and len(stack)>1 and stack[-2].tag == 'rr_nodes':
            if node.get('type') in ['CHANX', 'CHANY'] and int(node.get('capacity'))>0:
                loc, segment = node.find('loc'), node.find('segment')
                cap, keys = int(node.get('capacity')), []
                for x in range(int(loc.get('xlow')), int(loc.get('xhigh'))+1):
                    for y in range(int(loc.get('ylow')), int(loc.get('yhigh'))+1):
                        key = (int(loc.get('layer', '0')), x, y, node.get('type'), int(segment.get('segment_id')) if segment is not None else -1)
                        keys.append(key)
                        bins[key] = bins.get(key, 0)+cap
                channels.append((int(node.get('id')), cap, keys))
            stack[-2].remove(node)
            node.clear()
        if node.tag == 'rr_nodes':
            break
        stack.pop()
    assert len(channels)==258720 and len(bins)==17160
    bindings[str(graph)] = sha(graph)
    rows = []
    for i in range(1, 4):
        case = f'episode_{i:02d}'
        model = source/case/'model/sketch.json'
        for proof, flag in [(source/case/'sketch_verification.json', 'all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'),
                            (source/case/'events_verification.json', 'complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass')]:
            verification = json.loads(proof.read_text())
            assert verification[flag] and verification['bindings'][str(model)] == sha(model)
            bindings[str(proof)] = sha(proof)
        pred = {int(k): v for k, v in json.loads(model.read_text())['ledger'].items()}
        truth_path = R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/case/'cold/physical_audit.json'
        assert results['bindings'][str(truth_path)] == sha(truth_path)
        truth = {int(k): v for k, v in json.loads(truth_path.read_text())['node_occupancy'].items()}
        sp, st = Counter(), Counter()
        for n, cap, keys in channels:
            for key in keys:
                sp[key] += pred.get(n, 0)
                st[key] += truth.get(n, 0)
        metrics = dict(concrete=compare({n:Fraction(pred.get(n,0), cap) for n,cap,_ in channels}, {n:Fraction(truth.get(n,0),cap) for n,cap,_ in channels},12936),
                       spatial=compare({k:Fraction(sp[k],cap) for k,cap in bins.items()}, {k:Fraction(st[k],cap) for k,cap in bins.items()},20))
        old = next(row for row in results['cases'] if row['case']==case)
        comparisons = {}
        for candidate in ['static_criticality', 'NET_tree_ensemble']:
            checks = []
            for scope in ['concrete', 'spatial']:
                for metric in ['spearman', 'precision_at_k']:
                    x, y = old['metrics'][candidate][scope][metric], metrics[scope][metric]
                    eps = 1e-12 if metric=='spearman' else 0
                    checks.append(dict(scope=scope,metric=metric,candidate=x,control=y,nonregression=x>=y-eps,strict=x>y+eps))
            comparisons[candidate] = dict(checks=checks, raw_min_on_comparison_pass=all(c['nonregression'] for c in checks) and any(c['strict'] for c in checks))
        rows.append(dict(case=case, raw_min_on_metrics=metrics, comparisons=comparisons))
        bindings.update({str(p):sha(p) for p in [model,truth_path]})
        print('RAW_MIN_ON_COLD_SCORED',case,flush=True)
    (out/'results.json').write_text(json.dumps(dict(status='ALL3_MISSING_CONTROL_COLD_METRICS_COMPUTED_INDEPENDENT_METRICS_PENDING',rows=rows,bindings=bindings,
        scope='Supplement to immutable prior cold scores. Same full resource/spatial domains, normalization, ties and four metrics. Static candidate already fails previous_native; this control cannot reverse that failure. No full original gate promotion or native utility claim.'),indent=2,default=lambda x: str(x) if isinstance(x,Fraction) else None)+'\n')


if __name__ == '__main__':
    main()
