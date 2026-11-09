"""Label-consuming spatial evaluator for the separately frozen bbox control."""
import json,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from stream_metric_domain import metric_domain
from prediction_metrics import compare

parent=Path('experiments/koios_geometry_control_2026-10-05');out=Path('experiments/koios_geometry_evaluation_2026-10-05');native=Path('experiments/koios_spmv_native_path_audit_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());nr=json.loads((native/'receipt.json').read_text())
assert r['protocol_sha256']==sha(parent/'protocol.json') and r['inputs_unchanged']
assert all(sha(parent/f)==s for f,s in r['outputs'].items())
assert sha(native/'native.json')==nr['native_sha256']
assert all(sha(v['path'])==v['sha256'] for v in p['inputs'].values())
inputs={**p['inputs'],'native':{'path':str((native/'native.json').resolve()),'sha256':sha(native/'native.json')},'geometry_prediction':{'path':str((parent/'spatial_prediction.json').resolve()),'sha256':r['outputs']['spatial_prediction.json']}}
out.mkdir();(out/'source').mkdir()
for f in ['evaluate_koios_geometry.py','stream_metric_domain.py','prediction_metrics.py','pre_route_endpoints.py']:shutil.copy2(Path('tools')/f,out/'source'/f)
protocol={'inputs':inputs,'source_sha256':{f.name:sha(f) for f in (out/'source').iterdir()},'metrics':'spatial Spearman/MAE/top20 original descending value then ascending string key; no parameter changes','scope':'simple endpoint-bbox control, spatial metrics only; single Koios design/seed'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
truth=json.loads((native/'native.json').read_text());_,_,_,spatial_truth,_,_=metric_domain(inputs['rr_graph.xml']['path'],{},truth['node_occupancy'])
values=json.loads((parent/'spatial_prediction.json').read_text());assert set(values)==set(spatial_truth)
report=compare(values,spatial_truth,20)
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
receipt={'protocol_sha256':sha(out/'protocol.json'),'inputs_unchanged':True,'identical_spatial_domain':True,'spatial':report,'evaluation_s':time.monotonic()-start,'scope':protocol['scope'],'interpretation':'no resource-node prediction/physical routing/quality gain/feedback/acceleration claim'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
