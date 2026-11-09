"""Evaluator-only per-net wirelength/sharing gap, never a predictor input."""
import json,time
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
start=time.monotonic();out=Path('experiments/alu4_span_gap_diagnostic_2026-10-05');assert not out.exists()
files={'graph':'work/alu4_validation_capture_2026-10-05/rr_graph.xml','prediction':'experiments/alu4_incremental_budget_cohort_prepared_2026-10-05/prediction.json','native_audit':'experiments/alu4_transfer_evaluation_2026-10-05/native_audit.json','native_route':'work/alu4_validation_capture_2026-10-05/alu4.route','endpoints':'experiments/alu4_validation_capture_2026-10-05/endpoints.json','comparison':'experiments/alu4_budget_native_comparison_2026-10-05/receipt.json'};inputs={p:sha(p) for p in files.values()};g=read_rr_graph(files['graph']);pred=json.loads(Path(files['prediction']).read_text());native=json.loads(Path(files['native_audit']).read_text());ep=json.loads(Path(files['endpoints']).read_text());comparison=json.loads(Path(files['comparison']).read_text());assert native['route_sha256']==inputs[files['native_route']] and native['graph_sha256']==g.sha256
key=lambda r:(r['net_id'],r['source'],r['sink']);assert Counter(map(key,pred['connections']))==Counter(map(key,native['connections']))
spans={}
for n,node in g.nodes.items():
 loc=dict(node.location);spans[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1 if node.type in {'CHANX','CHANY'} else 0
def measure(rows,edgekey):
 groups=defaultdict(list)
 for r in rows:groups[r['net_id']].append(r)
 result={}
 for net,connections in groups.items():
  union=set();expanded=0
  for r in connections:
   nodes={g.edges[eid].sink for eid in r[edgekey]};union.update(nodes);expanded+=sum(spans[n] for n in nodes)
  length=sum(spans[n] for n in union);result[net]={'fanout':len(connections),'union_span':length,'connection_expanded_span':expanded,'shared_span_saved':expanded-length}
 return result
p=measure(pred['connections'],'physical_edge_ids');b=measure(native['connections'],'edge_ids');assert set(p)==set(b)
records=[{'net_id':net,'net_name':ep['net_names'][str(net)],'fanout':p[net]['fanout'],'native':b[net],'prediction':p[net],'union_span_delta':p[net]['union_span']-b[net]['union_span'],'expanded_span_delta':p[net]['connection_expanded_span']-b[net]['connection_expanded_span'],'sharing_saved_delta':p[net]['shared_span_saved']-b[net]['shared_span_saved']} for net in sorted(p)]
for r in records:assert r['union_span_delta']==r['expanded_span_delta']-r['sharing_saved_delta']
assert sum(x['union_span'] for x in p.values())==comparison['routecast']['wirelength'];assert sum(x['union_span'] for x in b.values())==comparison['baseline']['wirelength'];assert sum(r['union_span_delta'] for r in records)==4591
cohort=[r for r in records if r['fanout']>=64];other=[r for r in records if r['fanout']<64]
summary={'total_gap':4591,'high_fanout_nets':len(cohort),'high_fanout_gap':sum(r['union_span_delta'] for r in cohort),'other_nets':len(other),'other_gap':sum(r['union_span_delta'] for r in other),'expanded_span_delta':sum(r['expanded_span_delta'] for r in records),'sharing_saved_delta':sum(r['sharing_saved_delta'] for r in records),'top10_by_gap':sorted(records,key=lambda r:(-r['union_span_delta'],r['net_id']))[:10]}
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'nets.json').write_text(json.dumps(records,indent=2)+'\n');r={'summary':summary,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'nets_sha256':sha(out/'nets.json'),'wall_s':time.monotonic()-start,'scope':'Posthoc evaluator-only accounting; expansion/sharing arithmetic is not causal attribution, native pin permutations differ and no algorithm retuning or unseen claim'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(summary),flush=True)
