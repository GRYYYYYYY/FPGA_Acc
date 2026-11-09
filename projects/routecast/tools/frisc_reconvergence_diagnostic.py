import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
out=Path('experiments/frisc_reconvergence_diagnostic_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files={'prediction':'experiments/frisc_sequential_pin_descending_2026-10-05/prediction.json','receipt':'experiments/frisc_sequential_pin_descending_2026-10-05/receipt.json','baseline':'experiments/frisc_timing_backgrounds_v2_2026-10-05/baseline_prediction.json','endpoints':'experiments/frisc_endpoints_2026-10-05/endpoints.json','graph':'work/frisc_graph_capture_2026-10-05/rr_graph.xml'}
inputs={p:sha(p) for p in files.values()};g=read_rr_graph(files['graph']);pred=json.loads(Path(files['prediction']).read_text());e=json.loads(Path(files['endpoints']).read_text());audit(g,e,pred);baseline={r['connection_id']:r for r in json.loads(Path(files['baseline']).read_text())['connections']};receipt=json.loads(Path(files['receipt']).read_text());bad=[r for r in receipt['topology_after']['nets'] if r['internal_multi_incoming_nodes']];reports=[]
for net in bad:
 for n in net['internal_multi_incoming_nodes']:
  arrivals=defaultdict(list)
  for r in pred['connections']:
   if r['net_id']!=net['net_id']:continue
   for pos,eid in enumerate(r['physical_edge_ids']):
    edge=g.edges[eid]
    if edge.sink==n:
     arrivals[eid].append({'cid':r['connection_id'],'source':r['source'],'sink':r['sink'],'method':r['method'],'changed_from_baseline':r['physical_edge_ids']!=baseline[r['connection_id']]['physical_edge_ids'],'prefix_edge_ids':r['physical_edge_ids'][:pos+1],'suffix_edge_ids':r['physical_edge_ids'][pos+1:]})
  assert len(arrivals)>1
  reports.append({'net_id':net['net_id'],'rr_node':n,'node_type':g.nodes[n].type,'incoming_edges':[{'edge_id':eid,'source_rr':g.edges[eid].source,'switch_id':g.edges[eid].switch_id,'connections':rows} for eid,rows in sorted(arrivals.items())]})
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());result={'reports':reports,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'scope':'post-hoc exact incoming-arc/connection attribution; no automatic tree repair or native timing claim'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps([{'net':r['net_id'],'node':r['rr_node'],'type':r['node_type'],'arrivals':[{'edge':v['edge_id'],'connections':[(c['cid'],c['method'],c['changed_from_baseline']) for c in v['connections']]} for v in r['incoming_edges']]} for r in reports]))
