"""Separate evaluator: native printed node union vs frozen predictor outputs."""
import argparse,hashlib,json,re
from collections import defaultdict
from pathlib import Path
from rr_graph import read_rr_graph
from pin_template_trial import spatial
from prediction_metrics import compare
from native_node_labels import node_labels

p=argparse.ArgumentParser();p.add_argument('experiment',type=Path);p.add_argument('route',type=Path);a=p.parse_args()
root=a.experiment;protocol=json.loads((root/'protocol.json').read_text());receipt=json.loads((root/'receipt.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
if sha(root/'protocol.json')!=receipt['protocol_sha256']:raise ValueError('protocol changed')
for entry in protocol['inputs'].values():
    if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
g=read_rr_graph(protocol['inputs']['graph']['path'])
e=json.loads(Path(protocol['inputs']['endpoints']['path']).read_text())
truth=node_labels(g,a.route,e['inputs']['place']['sha256'])
resources=[n for n,node in g.nodes.items() if node.type in {'CHANX','CHANY'} and node.capacity]
reports={}
for name in ['raw.json']+[f'hybrid_{"fixed" if r is None else r}.json' for r in protocol['variants']]:
    if sha(root/name)!=receipt['artifacts'][name]:raise ValueError('prediction artifact changed')
    pred=json.loads((root/name).read_text());values=pred['node_occupancy']
    reports[name]={'spatial':compare(spatial(g,values),spatial(g,truth),20),'resource':compare({str(n):values.get(str(n),0)/g.nodes[n].capacity for n in resources},{str(n):truth.get(str(n),0)/g.nodes[n].capacity for n in resources},max(1,len(resources)//20))}
result={'scope':'single clma frozen final-route descriptive evaluation, no process-overflow or feedback evidence','route_sha256':sha(a.route),'protocol_sha256':receipt['protocol_sha256'],'reports':reports,'evaluator_sha256':sha(__file__),'native_label_source_sha256':sha(Path(__file__).with_name('native_node_labels.py'))}
(root/'final_route_evaluation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(reports))
