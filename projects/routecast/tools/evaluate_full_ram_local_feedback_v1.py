"""Complete-cohort frozen-pressure comparison; preserve negative results."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from prediction_metrics import compare
from stream_metric_domain import metric_domain
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'full_ram_local_feedback_comparison_v1_2026-10-09';D.mkdir(exist_ok=False)
P=E/'full_ram_local_feedback_v2_2026-10-09';B=E/'full_ram_length_switch_prediction_v1_2026-10-09'
files=[P/'receipt.json',B/'receipt.json',E/'full_ram_local_feedback_verification_v1_2026-10-09/verification.json']
for file in files:
    obj=json.loads(file.read_text())
    if file.name=='receipt.json':assert obj['status'] in ('COMPLETE_AUDITED_PREDICTION','COMPLETE_AUDITED_LOCAL_FEEDBACK')
    else:assert obj['passed']
    for p,h in {**obj['bindings'],**obj.get('files',{})}.items():assert sha(p)==h
pred=json.loads((P/'prediction.json').read_text());base=json.loads((B/'prediction.json').read_text())
assert pred['completed']==base['completed']==16819
graph=E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml'
truthfile=E/'full_ram_comb_only_route_audit_v1_2026-10-09/physical_audit.json';truth=json.loads(truthfile.read_text())
_,_,pressure,st,caps,_=metric_domain(graph,pred['node_occupancy'],truth['node_occupancy'])
_,_,length,bt,_,_=metric_domain(graph,base['node_occupancy'],truth['node_occupancy']);assert st==bt
geometryfile=E/'full_ram_geometry_control_v1_2026-10-09/spatial_prediction.json';geometry=json.loads(geometryfile.read_text());assert set(st)==set(geometry)
old={c['connection_id']:c for c in base['connections']};changed=0
for c in pred['connections']:
    prior=old[c['connection_id']]
    assert all(c[k]==prior[k] for k in ('connection_id','net_id','source','sink'))
    changed+=c['physical_edge_ids']!=prior['physical_edge_ids']
over={n:v-caps[n] for n,v in pred['node_occupancy'].items() if v>caps[n]}
receipt=json.loads((P/'receipt.json').read_text())
paths=[Path(__file__),*files,P/'prediction.json',B/'prediction.json',graph,truthfile,geometryfile,R/'tools/prediction_metrics.py',R/'tools/stream_metric_domain.py']
out=dict(pressure=compare(pressure,st,20),length_switch=compare(length,st,20),geometry=compare(geometry,st,20),
    changed_paths=changed,overused_prediction_nodes=len(over),prediction_excess_occupancy=sum(over.values()),
    pressure_costs=receipt['details'],total_pressure_seconds=receipt['total_s'],bindings={str(p):sha(p) for p in paths},
    scope='Complete 16819-connection, identical 2400-bin development comparison; local whole-net own-excluded pressure update, rest original paths retained; not global updated optimization. Not negotiated routing, independent family, or matched end-to-end benefit.')
(D/'comparison.json').write_text(json.dumps(out,indent=2)+'\n');print(out['pressure'],changed,len(over),out['prediction_excess_occupancy'])
