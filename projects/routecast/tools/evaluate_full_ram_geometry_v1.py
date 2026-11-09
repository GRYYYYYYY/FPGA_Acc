"""Label-consuming spatial evaluation, isolated from the input-only predictor."""
import hashlib,json,time
from pathlib import Path
from prediction_metrics import compare
from stream_metric_domain import metric_domain
R=Path(__file__).resolve().parents[1];E=R/'experiments'
B=E/'full_ram_geometry_control_v1_2026-10-09';D=E/'full_ram_geometry_evaluation_v1_2026-10-09';D.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((B/'protocol.json').read_text());r=json.loads((B/'receipt.json').read_text())
assert r['protocol_sha256']==sha(B/'protocol.json') and r['inputs_unchanged']
for name,h in r['outputs'].items():assert sha(B/name)==h
for v in p['inputs'].values():assert sha(Path(v['path']))==v['sha256']
truthfile=E/'full_ram_comb_only_route_audit_v1_2026-10-09/physical_audit.json'
alignment=truthfile.parent/'alignment.json';a=json.loads(alignment.read_text());assert a['passed']
for path,h in a['bindings'].items():assert sha(Path(path))==h
graph=Path(p['inputs']['rr_graph.xml']['path']);prediction=B/'spatial_prediction.json'
bindings={str(path):sha(path) for path in [Path(__file__),B/'protocol.json',B/'receipt.json',graph,prediction,truthfile,alignment,R/'tools/prediction_metrics.py',R/'tools/stream_metric_domain.py']}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,metrics='All identical string-key spatial bins: Spearman, MAE, top20 precision/recall with original lexicographic tie rule.',scope='Full cw192 single development design/seed, comb-only native constants. Labels opened only by evaluator; no unseen-family generalization or route benefit claim.'),indent=2)+'\n')
t=time.perf_counter();truth=json.loads(truthfile.read_text())
assert truth['inputs_sha256']['graph']==sha(graph) and truth['overflow_units']==0
_,_,_,spatial,_,_=metric_domain(graph,{},truth['node_occupancy'])
predicted=json.loads(prediction.read_text());assert set(predicted)==set(spatial)
result=compare(predicted,spatial,20)
(D/'vectors.json').write_text(json.dumps([dict(key=k,prediction=predicted[k],truth=spatial[k]) for k in sorted(spatial)],indent=2)+'\n')
out=dict(bindings=bindings,spatial=result,evaluation_s=time.perf_counter()-t,vectors_sha256=sha(D/'vectors.json'),admitted_as_unseen_family=False)
(D/'evaluation.json').write_text(json.dumps(out,indent=2)+'\n');print(result)
