"""Fixture checks for frozen two-frame evaluation, not neuron label evidence."""
import json
import tempfile
from pathlib import Path
from neuron_complete_prediction_metrics_v1 import evaluate
from pre_route_endpoints import sha


def main():
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'graph.xml'
        p.write_text('<rr_graph><rr_nodes>'+''.join(f'<node id="{i}" type="CHANX" capacity="1"><loc layer="0" xlow="{i}" xhigh="{i}" ylow="0" yhigh="0"/><segment segment_id="0"/></node>' for i in range(40))+'</rr_nodes></rr_graph>')
        rows=evaluate(p,{'0':1},{'1':1},{'1':1})['metrics']
        for frame in rows.values():
            assert frame['concrete']['universe_size']==40
            assert frame['concrete']['k']==2
            assert frame['spatial']['universe_size']==40
            assert frame['spatial']['k']==20
        assert rows['sketch']['concrete']['spearman']==1
        assert rows['sketch']['concrete']['mae']==0
        assert rows['initial']['concrete']['mae']==.05
        constant=evaluate(p,{},{},{})['metrics']
        for frame in constant.values():
            for key in ('concrete','spatial'):
                assert frame[key]['spearman'] is None
                assert frame[key]['mae']==0 and frame[key]['nonzero_truth']==0
    base=Path(__file__).resolve().parent
    bindings={str(base/name):sha(base/name) for name in (Path(__file__).name,'neuron_complete_prediction_metrics_v1.py','stream_metric_domain_layered_v1.py','prediction_metrics.py','pre_route_endpoints.py')}
    out=base.parent/'experiments/neuron_metric_entry_contract_v1_2026-10-14';out.mkdir(exist_ok=True)
    report=dict(all_pass=True,bindings=bindings,complete_zero_resources=True,frozen_channel_k=2,frozen_spatial_k=20,constant_correlation_is_explicit_null=True,scope='40-channel fixture only; native neuron truth not supplied or accepted.')
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS complete universes, fixed k, two frames, null constant correlations')

if __name__=='__main__':main()
