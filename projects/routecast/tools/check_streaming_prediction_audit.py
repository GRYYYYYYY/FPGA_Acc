import json,time,shutil
from pathlib import Path
from streaming_prediction_audit import verify
from physical_prediction_audit import audit
from feedback_scores import scores
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
out=Path('experiments/clma_streaming_prediction_audit_2026-10-05')
if out.exists():raise ValueError('fresh output required')
out.mkdir();shutil.copyfile(__file__,out/'driver.py');shutil.copyfile('tools/streaming_prediction_audit.py',out/'auditor.py')
p=json.loads(Path('experiments/clma_cost_binding_2026-10-04/protocol.json').read_text());graph=p['inputs']['graph']['path'];path=Path('experiments/clma_full_goal_astar_2026-10-04/prediction.json');prediction=json.loads(path.read_text())
e={'graph_sha256':prediction['physical_graph_sha256'],'connections':[{k:r[k] for k in ('connection_id','net_id','source','sink')} for r in prediction['connections']]}
inputs={graph:sha(graph),str(path):sha(path)};start=time.monotonic();actual=verify(graph,e,prediction);g=read_rr_graph(graph);expected=audit(g,e,prediction)
for key,value in expected.items():
 if key!='scope':assert actual[key]==value,(key,actual[key],value)
f=scores(g,e,prediction['node_occupancy']);assert actual['channel_net_span_sum']==f['channel_net_span_sum'] and actual['predicted_channel_overuse_units']==f['predicted_channel_overuse_units']
assert all(sha(p)==h for p,h in inputs.items())
receipt={'all_existing_audit_fields_equal':True,'feedback_span_and_overuse_equal':True,'result':actual,'inputs':inputs,'source_sha256':sha(out/'auditor.py'),'wall_s':time.monotonic()-start,'scope':'same original XML witnesses compared with old audit; endpoints here derived from prediction, not independent mapping validation'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
