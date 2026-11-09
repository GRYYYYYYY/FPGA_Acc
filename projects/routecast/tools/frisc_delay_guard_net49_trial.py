"""Fixed fanout cohort, current-background net batches, capacity and tree gated."""
import json,time
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from weighted_pin_candidates import WeightedPins
from buffered_delay_cost import BufferedDelayCost
from net_union_topology import diagnose
from net_union_commit_gate import check
from net_pressure_sketch import net_union
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
from feedback_scores import scores
from physical_prediction_audit import audit
start=time.monotonic();out=Path('experiments/frisc_delay_guard_net49_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files={'prediction':'experiments/frisc_shared_trunk_gated_candidate_2026-10-05/prediction.json','graph':'work/frisc_graph_capture_2026-10-05/rr_graph.xml','endpoints':'experiments/frisc_endpoints_2026-10-05/endpoints.json'};inputs={p:sha(p) for p in files.values()};current=json.loads(Path(files['prediction']).read_text());groups=defaultdict(list)
for r in current['connections']:groups[r['net_id']].append(r)
cohort=[49];out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'search.py').write_text(Path('tools/weighted_pin_candidates.py').read_text());protocol={'input_sha256':inputs,'net_ids':cohort,'requests':{n:len(groups[n]) for n in cohort},'development_case':'net49 selected after previous native regression diagnosis; not prospective unseen-design evaluation','policy':'ascending net ID and CID; fixed existing physical pins; block saturated other-net channels; marginal trunk span*10000 plus path span; prohibit all alternative incoming arcs into built nodes; net failure or non-improvement retains current state; publish whole-net atomic batch only if zero channel overuse and strictly lower total span','native_label_inputs':False,'electrical_policy':'exact additive buffered zero-Cinternal delay primary; marginal span secondary; each connection delay must not exceed its old delay','search_stop_rule':'one current physical IPIN, exhaust equal-cost frontier; stop only after no unsettled lower bound can improve its terminal cost'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');g=read_rr_graph(files['graph']);engine=WeightedPins(g);e=json.loads(Path(files['endpoints']).read_text());audit(g,e,current);ledger=LocalBatchOccupancy(g)
for r in current['connections']:assert ledger.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
span={};incoming=defaultdict(list)
for eid,edge in enumerate(g.edges):incoming[edge.sink].append(eid)
for n,node in g.nodes.items():
 loc=dict(node.location);span[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1 if node.type in {'CHANX','CHANY'} else 0
delay_model=BufferedDelayCost(g);delay_factor=(len(g.nodes)-1)*max(span.values())*10001+1
(out/'delay_cost.py').write_text(Path('tools/buffered_delay_cost.py').read_text())
baseline=scores(g,e,current['node_occupancy']);now=baseline;reports=[];attempts=[]
for net in cohort:
 tnet=time.monotonic();rows=sorted([r for r in current['connections'] if r['net_id']==net],key=lambda r:r['connection_id']);users,demand=net_union(g,current);blocked={n for n,node in g.nodes.items() if node.type in {'CHANX','CHANY'} and demand.get(n,0)-int(n in users[net])>=node.capacity};built=set();staged=[];forbidden=set();tree_incoming={};queries=[];failure=None
 for old in rows:
  w=engine.catalog.witness(old['source'],old['sink'],old['physical_edge_ids']);costs=[delay_model.weights[eid]*delay_factor+span[edge.sink]*(1+(0 if edge.sink in built else 10000)) for eid,edge in enumerate(g.edges)];t=time.monotonic();r=engine.query(old['source'],old['sink'],w['selected_opin_ptc'],costs,blocked,forbidden,target_pins={w['selected_ipin_ptc']});path=r['paths'].get(w['selected_ipin_ptc']);q={'cid':old['connection_id'],'query_s':time.monotonic()-t,'same_pin_reachable':path is not None}
  if path is None:failure='same physical input pin unreachable';queries.append(q);break
  old_delay=delay_model.path_delay(old['source'],old['physical_edge_ids']);new_delay=delay_model.path_delay(old['source'],path);q['old_delay_ns']=float(old_delay*10**9);q['new_delay_ns']=float(new_delay*10**9)
  if new_delay>old_delay:failure='minimum-delay reachable candidate exceeds original per-connection delay budget';queries.append(q);break
  new={**old,'physical_edge_ids':path,'method':'shared_trunk_batch'};nw=engine.catalog.witness(new['source'],new['sink'],path);assert nw['selected_ipin_ptc']==w['selected_ipin_ptc'] and nw['selected_opin_ptc']==w['selected_opin_ptc'];assert all(g.edges[a].sink not in blocked for a in path) and not set(path)&forbidden
  top=diagnose(g,{'physical_graph_sha256':g.sha256,'connections':staged+[new]});bad=[x for x in top['nets'] if x['internal_multi_incoming_nodes'] or x['cyclic_union'] or x['source_has_incoming'] or not x['all_nodes_source_reachable']];q['partial_tree_accepted']=not bad
  if bad:failure='partial tree incompatible';q['rejected_nets']=bad;queries.append(q);break
  staged.append(new);built.update(g.edges[a].sink for a in path)
  for eid in path:
   edge=g.edges[eid]
   if edge.sink in tree_incoming:assert tree_incoming[edge.sink]==eid
   else:tree_incoming[edge.sink]=eid;forbidden.update(other for other in incoming[edge.sink] if other!=eid)
  queries.append(q);print(json.dumps({'net':net,'completed':len(staged),'total':len(rows)}),flush=True)
 report={'net':net,'requested':len(rows),'built':len(staged),'failure':failure,'queries':queries,'committed':False,'before_scores':now};attempts.append({'net':net,'candidate_paths':staged})
 if failure is None:
  gate=check(g,current,staged);report['whole_net_gate']=gate;assert gate['accepted'];branch=ledger.fork();updates=[{**{k:r[k] for k in ('connection_id','net_id','source','sink')},'epoch':2,'edge_ids':r['physical_edge_ids']} for r in staged];assert branch.update_batch(updates)==Result.COMMITTED;after=scores(g,e,{str(n):v for n,v in branch.occupancy.items() if v});report['candidate_scores']=after;assert after['predicted_channel_overuse_units']==0
  if after['channel_net_span_sum']<now['channel_net_span_sum']:
   replacements={r['connection_id']:r for r in staged};newrows=[replacements.get(r['connection_id'],r) for r in current['connections']];ledger=branch;current={'physical_graph_sha256':g.sha256,'connections':newrows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'methods':dict(Counter(r['method'] for r in newrows)),'requested':len(newrows),'completed':len(newrows)};now=after;report['committed']=True
 report['wall_s']=time.monotonic()-tnet;reports.append(report);(out/'progress.json').write_text(json.dumps(reports)+'\n');(out/'checkpoint_prediction.json').write_text(json.dumps(current)+'\n');print(json.dumps({'net_done':net,'failure':failure,'committed':report['committed'],'scores':now}),flush=True)
checked=audit(g,e,current);top=diagnose(g,current);assert all(not r['internal_multi_incoming_nodes'] and not r['cyclic_union'] and not r['source_has_incoming'] and r['all_nodes_source_reachable'] for r in top['nets']);assert all(sha(p)==h for p,h in inputs.items());(out/'prediction.json').write_text(json.dumps(current)+'\n');(out/'attempted_paths.json').write_text(json.dumps(attempts)+'\n');result={'baseline_scores':baseline,'final_scores':now,'reports':reports,'physical_audit':checked,'final_topology':top,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'search_sha256':sha(out/'search.py'),'protocol_sha256':sha(out/'protocol.json'),'prediction_sha256':sha(out/'prediction.json'),'attempted_paths_sha256':sha(out/'attempted_paths.json'),'full_wall_s':time.monotonic()-start,'scope':'posthoc net49 development pilot, electrical delay primary and per-connection budget; no native timing guarantee or unseen-family claim'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'baseline':baseline,'final':now,'committed_nets':sum(r['committed'] for r in reports),'failed_nets':sum(r['failure'] is not None for r in reports),'full_wall_s':result['full_wall_s']}),flush=True)
