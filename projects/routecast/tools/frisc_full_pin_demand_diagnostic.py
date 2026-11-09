"""Post-hoc simultaneous demand response, no policy retuning."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
from net_pressure_sketch import net_union
out=Path('experiments/frisc_full_pin_demand_diagnostic_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files={'before':'experiments/frisc_timing_backgrounds_v2_2026-10-05/baseline_prediction.json','after':'experiments/frisc_full_weighted_pin_commit_2026-10-05/prediction.json','endpoints':'experiments/frisc_endpoints_2026-10-05/endpoints.json','graph':'work/frisc_graph_capture_2026-10-05/rr_graph.xml'}
inputs={p:sha(p) for p in files.values()};start=time.monotonic();g=read_rr_graph(files['graph']);e=json.loads(Path(files['endpoints']).read_text());pred={k:json.loads(Path(files[k]).read_text()) for k in ('before','after')}
for p in pred.values():audit(g,e,p)
unions={k:net_union(g,p) for k,p in pred.items()};bu,bd=unions['before'];au,ad=unions['after'];assert set(bu)==set(au)
records=[];summary={k:0 for k in ('span_delta','overuse_delta','newly_overloaded_channels','newly_overloaded_overuse','previously_overloaded_overuse_delta','remaining_nonoverloaded_delta')}
for n,node in g.nodes.items():
 if node.type not in {'CHANX','CHANY'}:continue
 old=bd.get(n,0);new=ad.get(n,0);c=node.capacity;before=max(0,old-c);after=max(0,new-c)
 if old==new:continue
 loc=dict(node.location);span=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1
 record={'rr_node':n,'capacity':c,'before_demand':old,'after_demand':new,'span_delta':(new-old)*span,'overuse_delta':after-before}
 records.append(record);summary['span_delta']+=record['span_delta'];summary['overuse_delta']+=record['overuse_delta']
 if before==0 and after>0:summary['newly_overloaded_channels']+=1;summary['newly_overloaded_overuse']+=after
 elif before>0:summary['previously_overloaded_overuse_delta']+=after-before
 else:summary['remaining_nonoverloaded_delta']+=after-before
assert summary['span_delta']==11411 and summary['overuse_delta']==813
# Explicit unique-net arrivals/departures on every changed channel.
arrivals={};departures={}
for net in bu:
 for n in au[net]-bu[net]:
  if g.nodes[n].type in {'CHANX','CHANY'}:arrivals.setdefault(n,[]).append(net)
 for n in bu[net]-au[net]:
  if g.nodes[n].type in {'CHANX','CHANY'}:departures.setdefault(n,[]).append(net)
for r in records:
 n=r['rr_node'];r['arriving_net_ids']=arrivals.get(n,[]);r['departing_net_ids']=departures.get(n,[]);assert r['after_demand']-r['before_demand']==len(r['arriving_net_ids'])-len(r['departing_net_ids'])
summary['newly_overloaded_with_multiple_arrivals']=sum(r['before_demand']<=r['capacity']<r['after_demand'] and len(r['arriving_net_ids'])>1 for r in records)
assert summary['overuse_delta']==summary['newly_overloaded_overuse']+summary['previously_overloaded_overuse_delta']+summary['remaining_nonoverloaded_delta']
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'channel_changes.json').write_text(json.dumps(records)+'\n');receipt={'summary':summary,'changed_channels':len(records),'full_wall_s':time.monotonic()-start,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'channel_changes_sha256':sha(out/'channel_changes.json'),'scope':'post-hoc exact unique-net channel arrival/departure decomposition; no causal timing or prospective improvement proof'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
