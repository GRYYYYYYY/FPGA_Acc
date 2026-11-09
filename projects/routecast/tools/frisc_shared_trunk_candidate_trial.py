"""Development pilot: highest endpoint fanout, fixed pins, legal-capacity trunk reuse."""
import json,time
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from weighted_pin_candidates import WeightedPins
from net_union_topology import diagnose
from net_union_commit_gate import check
from net_pressure_sketch import net_union
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
from feedback_scores import scores
from physical_prediction_audit import audit
start=time.monotonic();out=Path('experiments/frisc_shared_trunk_candidate_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files={'prediction':'experiments/frisc_final_one_candidate_commit_2026-10-05/prediction.json','graph':'work/frisc_graph_capture_2026-10-05/rr_graph.xml','endpoints':'experiments/frisc_endpoints_2026-10-05/endpoints.json'};inputs={p:sha(p) for p in files.values()};p=json.loads(Path(files['prediction']).read_text());groups=defaultdict(list)
for r in p['connections']:groups[r['net_id']].append(r)
net=min(groups,key=lambda n:(-len(groups[n]),n));selected=sorted(groups[net],key=lambda r:r['connection_id']);out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'protocol.json').write_text(json.dumps({'input_sha256':inputs,'selected_net':net,'requests':len(selected),'policy':'largest endpoint fanout, net ID tie break; ascending CID; current physical pins fixed; all other-net saturated channels blocked; new trunk marginal span*10000 plus path span; fail explicitly on unavailable same pin or partial tree incompatibility; publish only full whole-net legal-capacity strict span improvement','native_label_inputs':False},indent=2)+'\n');g=read_rr_graph(files['graph']);engine=WeightedPins(g);users,demand=net_union(g,p);blocked={n for n,node in g.nodes.items() if node.type in {'CHANX','CHANY'} and demand.get(n,0)-int(n in users[net])>=node.capacity};span={}
for n,node in g.nodes.items():
 loc=dict(node.location);span[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1 if node.type in {'CHANX','CHANY'} else 0
built=set();staged=[];reports=[];failure=None
for old in selected:
 w=engine.catalog.witness(old['source'],old['sink'],old['physical_edge_ids']);costs=[span[edge.sink]*(1+(0 if edge.sink in built else 10000)) for edge in g.edges];t=time.monotonic();r=engine.query(old['source'],old['sink'],w['selected_opin_ptc'],costs,blocked);path=r['paths'].get(w['selected_ipin_ptc']);report={'cid':old['connection_id'],'query_s':time.monotonic()-t,'same_pin_reachable':path is not None}
 if path is None:failure='same physical input pin unreachable';reports.append(report);break
 candidate={**old,'physical_edge_ids':path,'method':'shared_trunk_rebuild'};top=diagnose(g,{'physical_graph_sha256':g.sha256,'connections':staged+[candidate]});bad=[x for x in top['nets'] if x['internal_multi_incoming_nodes'] or x['cyclic_union'] or x['source_has_incoming'] or not x['all_nodes_source_reachable']];report['partial_tree_accepted']=not bad
 if bad:failure='partial tree incompatible';report['rejected_nets']=bad;reports.append(report);break
 staged.append(candidate);built.update(g.edges[e].sink for e in path);reports.append(report);print(json.dumps({'completed':len(staged),'total':len(selected),'net':net}),flush=True);(out/'progress.json').write_text(json.dumps(reports)+'\n')
result={'selected_net':net,'requested':len(selected),'built':len(staged),'failure':failure,'reports':reports,'committed':False,'baseline_scores':scores(g,json.loads(Path(files['endpoints']).read_text()),p['node_occupancy'])}
if failure is None:
 gate=check(g,p,staged);assert gate['accepted'];ledger=LocalBatchOccupancy(g)
 for r in p['connections']:assert ledger.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
 updates=[{**{k:r[k] for k in ('connection_id','net_id','source','sink')},'epoch':2,'edge_ids':r['physical_edge_ids']} for r in staged];assert ledger.update_batch(updates)==Result.COMMITTED;replacements={r['connection_id']:r for r in staged};newrows=[replacements.get(r['connection_id'],r) for r in p['connections']];pred={'physical_graph_sha256':g.sha256,'connections':newrows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'methods':dict(Counter(r['method'] for r in newrows)),'requested':len(newrows),'completed':len(newrows)};e=json.loads(Path(files['endpoints']).read_text());result['physical_audit']=audit(g,e,pred);after=scores(g,e,pred['node_occupancy']);result['candidate_scores']=after;assert after['predicted_channel_overuse_units']==0
 if after['channel_net_span_sum']<result['baseline_scores']['channel_net_span_sum']:result['committed']=True;(out/'prediction.json').write_text(json.dumps(pred)+'\n');result['prediction_sha256']=sha(out/'prediction.json')
(out/'candidate_paths.json').write_text(json.dumps(staged)+'\n');assert all(sha(p)==h for p,h in inputs.items());result.update(input_sha256=inputs,source_sha256=sha(out/'source.py'),protocol_sha256=sha(out/'protocol.json'),search_sha256=sha('tools/weighted_pin_candidates.py'),candidate_paths_sha256=sha(out/'candidate_paths.json'),full_wall_s=time.monotonic()-start,scope='single structurally selected high-fanout net on developed instance; native legality/STA not executed for new candidate');(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('reports','input_sha256')}),flush=True)
