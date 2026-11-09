"""Development-only sharedNET/counting ablation/geometry/hard baseline comparison."""
import sys,json,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from rr_graph import read_rr_graph
from stream_native_route_audit import audit
from prediction_metrics import compare
from endpoint_bbox_demand_v1 import predict as geometry
out=R/'experiments/mcnc_soft_demand_feedback_v1_2026-10-07';begin=time.perf_counter();bindings=closure([Path(__file__)]);rows=[]
# Authenticate every prediction and audit before the evaluator opens native labels.
for name in ['bigkey','dsip','misex3']:
 w=out/name;vp=w/'verification.json';v=json.loads(vp.read_text());assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];bindings[str(vp)]=sha(vp);bindings.update(v['bindings'])
assert all(sha(k)==h for k,h in bindings.items());(out/'evaluation_protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Fixed two-round 50ps feedback over complete three-design development cohort; shared original seed predictor unchanged; no label-selected round; same original graph/placement/endpoints/native labels and identical capacity spatial bins. Complete soft demand can overflow and is not a legal route. Independent-count ablation exact same paths. Geometry is unfitted endpoint bbox only. Hard baseline complete-only scoring; partials null. No heldout-family or native feedback/workflow-gain claim.',metric_policy='concrete CHAN top5percent; spatial top20; descending demand then ascending tuple/node ID ties'),indent=2)+'\n')
for name in ['bigkey','dsip','misex3']:
 start=time.perf_counter();w=out/name;epfile=R/f'experiments/mcnc_prospective_v1_2026-10-07/{name}/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);g=read_rr_graph(graph);assert g.sha256==ep['graph_sha256'];c=json.loads((w/'sketch.json').read_text());geo,capacities=geometry(g.nodes,ep['connections']);channels=sorted(n for n,x in g.nodes.items() if x.capacity>0 and x.type in ('CHANX','CHANY'));ledgers={'shared_net':{int(n):v for n,v in c['ledger'].items()},'independent_connection':{int(n):v for n,v in c['independent_connection_ledger'].items()}};hardfile=epfile.parent/'candidate.json';hard=json.loads(hardfile.read_text());bindings[str(hardfile)]=sha(hardfile);hard_complete=hard['completed_connections']==hard['required_connections']
 if hard_complete:ledgers['archived_hard_capacity']={int(n):v for n,v in hard['ledger'].items()}
 # Geometry and current path predictions are materialized before this read.
 route=epfile.parent/'design.route';bindings[str(route)]=sha(route);native=audit(graph,route);assert native['overflow_units']==0;truth={int(n):v for n,v in native['node_occupancy'].items()};td=defaultdict(int);pd={method:defaultdict(int) for method in ledgers}
 for n in channels:
  node=g.nodes[n];loc=dict(node.location)
  for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
   for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
    k=(int(loc.get('layer','0')),x,y,node.type,node.segment_id if node.segment_id is not None else -1);td[k]+=truth.get(n,0)
    for method,ledger in ledgers.items():pd[method][k]+=ledger.get(n,0)
 metrics={method:dict(concrete=compare({n:ledger.get(n,0)/g.nodes[n].capacity for n in channels},{n:truth.get(n,0)/g.nodes[n].capacity for n in channels},max(1,len(channels)//20)),spatial=compare({k:pd[method][k]/cap for k,cap in capacities.items()},{k:td[k]/cap for k,cap in capacities.items()},20)) for method,ledger in ledgers.items()};metrics['geometry']=dict(concrete=None,spatial=compare(geo,{k:td[k]/cap for k,cap in capacities.items()},20))
 if not hard_complete:metrics['archived_hard_capacity']=dict(concrete=None,spatial=None)
 vectors=dict(channels=[dict(node=n,capacity=g.nodes[n].capacity,native=truth.get(n,0),predictions={m:l.get(n,0) for m,l in ledgers.items()}) for n in channels],bins=[dict(key=list(k),capacity=capacities[k],native=td[k],geometry=geo[k],predictions={m:pd[m][k] for m in ledgers}) for k in sorted(capacities)]);file=w/'comparison_vectors.json';file.write_text(json.dumps(vectors)+'\n');bindings[str(file)]=sha(file);paid=json.loads((w/'receipt.json').read_text())['total_paid_feedback_seconds'];rows.append(dict(name=name,completed=c['completed_connections'],required=c['required_connections'],overflow_units=c['overflow_units'],hard_completed=hard['completed_connections'],hard_required=hard['required_connections'],hard_scored=hard_complete,metrics=metrics,paid_feedback_only_seconds=paid,baseline_prediction_seconds=json.loads((R/f'experiments/mcnc_budgeted_soft_demand_v1_2026-10-07/{name}/receipt.json').read_text())['total_paid_prediction_seconds'],evaluation_seconds=time.perf_counter()-start));print('SOFT COMPARISON',name,{m:(round(x['spatial']['spearman'],4),x['spatial']['precision_at_k']) if x['spatial'] else None for m,x in metrics.items()},flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'comparison.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,total_evaluation_seconds=time.perf_counter()-begin,scope='Descriptive development comparison, no heldout retuning, legal route commit or complete workflow speed benefit.'),indent=2)+'\n')
