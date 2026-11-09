"""Frozen partial-result evaluator; never creates a complete-run receipt."""
import json
from pathlib import Path
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
from pin_template_trial import spatial
from prediction_metrics import compare

root=Path('experiments/clma_cross_design_2026-10-04');out=root/'partial_evaluation_0'
if out.exists():raise ValueError('fresh evaluation directory required')
p=json.loads((root/'protocol.json').read_text());paths={'graph':Path(p['inputs']['graph']['path']),'labels':root/'native_final_labels.json','raw':root/'raw.json','hybrid_0':root/'hybrid_0.json'}
out.mkdir();protocol={'scope':'raw and completed zero-round only; parent run still incomplete','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in paths.items()},'spatial_k':20,'resource_k':'5 percent, floor minimum 1','source_sha256':{n:sha(Path(__file__).with_name(n)) for n in ('evaluate_available_predictions.py','rr_graph.py','pin_template_trial.py','prediction_metrics.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
g=read_rr_graph(paths['graph']);labels=json.loads(paths['labels'].read_text())
if labels['graph_sha256']!=g.sha256:raise ValueError('label graph mismatch')
truth=labels['node_occupancy'];resources=[n for n,node in g.nodes.items() if node.type in {'CHANX','CHANY'} and node.capacity]
reports={}
for name in ('raw','hybrid_0'):
    pred=json.loads(paths[name].read_text());values=pred['node_occupancy']
    reports[name]={'spatial':compare(spatial(g,values),spatial(g,truth),20),'resource':compare({str(n):values.get(str(n),0)/g.nodes[n].capacity for n in resources},{str(n):truth.get(str(n),0)/g.nodes[n].capacity for n in resources},max(1,len(resources)//20))}
for entry in protocol['inputs'].values():
    if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'reports':reports,'scope':'partial parent-run descriptive final occupancy, no full-ablation or feedback claim'},indent=2)+'\n');print(json.dumps(reports),flush=True)
