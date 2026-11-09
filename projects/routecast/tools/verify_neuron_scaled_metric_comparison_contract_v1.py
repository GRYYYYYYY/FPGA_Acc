"""Complete-domain fixture and corruption checks, not large-factor evidence."""
import json
import resource
import tempfile
from pathlib import Path

from archive_design_exposure_v3 import sha
from neuron_scaled_present_frame_metrics_v1 import evaluate_frame, check_metric
from evaluate_neuron_scaled_present_full_comparison_v1 import owner_gone


def main():
    resource.setrlimit(resource.RLIMIT_AS, (192*2**20, 192*2**20))
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)/'graph.xml'
        nodes = [f'<node id="{i}" type="CHANX" capacity="{1+i%2}"><loc layer="{i%2}" xlow="{i}" xhigh="{i+1}" ylow="0" yhigh="0"/><segment segment_id="{i%3}"/></node>' for i in range(41)]
        nodes += ['<node id="41" type="SOURCE" capacity="1"><loc layer="0" xlow="0" xhigh="0" ylow="0" yhigh="0"/></node>',
                  '<node id="42" type="CHANX" capacity="0"><loc layer="0" xlow="0" xhigh="0" ylow="0" yhigh="0"/><segment segment_id="0"/></node>']
        xml = '<rr_graph><rr_nodes>'+''.join(nodes)+'</rr_nodes></rr_graph>'
        path.write_text(xml)
        p, t = {'1': 3, '10': 2, '41': 1}, {'10': 2, '20': 1, '41': 1}
        row = evaluate_frame(path, p, t)
        assert row['metrics']['concrete']['universe_size'] == 41
        assert row['metrics']['concrete']['k'] == 3  # ceil, not floor(41/20).
        assert row['metrics']['spatial']['universe_size'] == 82
        assert row['metrics']['spatial']['k'] == 20
        assert row['original_node_counts'] == {'CHANX': 42, 'SOURCE': 1}
        assert row['independent_Expat_domain_and_histogram_metrics_pass']
        for domain in evaluate_frame(path, {}, {})['metrics'].values():
            assert domain['spearman'] is None and domain['mae'] == 0
        rejected = 0
        for invalid in ({'0': True}, {'0': -1}, {0: 1}, {'999': 1}):
            try:
                evaluate_frame(path, invalid, {})
            except (ValueError, AssertionError):
                rejected += 1
            else:
                raise AssertionError('invalid occupancy accepted')
        for field in ('spearman', 'precision_at_k', 'mae', 'universe_size', 'truth_k_boundary'):
            fake = dict(evaluate_frame(path, {'0': 1}, {'0': 1})['metrics']['concrete'])
            fake[field] += 0.25
            # Reconstruct independent full domain explicitly for this simple fixture.
            pred = {str(i): 1.0 if i == 0 else 0.0 for i in range(41)}
            try:
                check_metric(pred, pred, fake, 3)
            except AssertionError:
                rejected += 1
            else:
                raise AssertionError('corrupted metric accepted: '+field)
        path.write_text(xml.replace('</rr_nodes>', nodes[0]+'</rr_nodes>'))
        try:
            evaluate_frame(path, {}, {})
        except AssertionError:
            rejected += 1
        else:
            raise AssertionError('duplicate channel accepted')
        assert rejected == 10
    assert owner_gone({'verified_live': False, 'status': 'missing_not_terminal_evidence'})
    assert owner_gone({'verified_identity': False, 'startticks': 20, 'state': 'R'})
    assert owner_gone({'verified_identity': True, 'state': 'Z'})
    assert not owner_gone({'verified_identity': True, 'state': 'R', 'verified_live': True})
    assert not owner_gone({'verified_live': False, 'status': 'invalid_process_metadata'})
    root = Path(__file__).resolve().parents[1]
    files = [Path(__file__), root/'tools/neuron_scaled_present_frame_metrics_v1.py',
             root/'tools/evaluate_neuron_scaled_present_full_comparison_v1.py',
             root/'tools/prediction_metrics.py', root/'tools/stream_metric_domain_layered_v1.py',
             root/'tools/diagnose_neuron_complete_metric_hotspots_v1.py']
    out = root/'experiments/neuron_scaled_metric_comparison_contract_v1_2026-10-15'
    out.mkdir()
    value = dict(bindings={str(p): sha(p) for p in files}, all_pass=True,
                 concrete_channels=41, spatial_bins=82, concrete_ceil_k=3,
                 invalid_input_or_metric_cases_rejected=10, queue_owner_guard_cases=5,
                 complete_layers_spans_zero_channels_and_constant_null_checked=True,
                 scope='Small complete-domain fixture and ten corruptions only. No large-factor metric evaluation, unseen-family, quality or workflow gain proved.')
    (out/'verification.json').write_text(json.dumps(value, indent=2)+'\n')
    print('PASS full-domain/layers/spans/zeros,10 corruptions,5 queue-owner guards; fixture only.')


if __name__ == '__main__':
    main()
