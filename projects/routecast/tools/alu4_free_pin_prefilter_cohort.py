"""Replace one branch with retained net trunk under exact original delay budget."""
import json,time
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from prepared_budget_pin_candidates import PreparedBudgetPins as BudgetPins
from buffered_delay_cost import BufferedDelayCost
from net_pressure_sketch import net_union
from net_union_commit_gate import check
from net_union_topology import diagnose
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
from physical_prediction_audit import audit
from feedback_scores import scores
from free_pin_budget_selection import choose
from local_channel_scores import LocalChannelScores
timings=Counter()
calls=Counter()
def measured(name,fn,*args,**kwargs):
 t=time.monotonic()
 try:return fn(*args,**kwargs)
 finally:timings[name]+=time.monotonic()-t;calls[name]+=1
start=time.monotonic();out=Path('experiments/alu4_free_pin_prefilter_cohort_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files={'prediction':'experiments/alu4_free_pin_budget_trial_2026-10-05/prediction.json','graph':'work/alu4_validation_capture_2026-10-05/rr_graph.xml','endpoints':'experiments/alu4_validation_capture_2026-10-05/endpoints.json','equivalence':'experiments/alu4_full_pin_equivalence_audit_2026-10-05/receipt.json'};inputs={p:sha(p) for p in files.values()};current=json.loads(Path(files['prediction']).read_text());fanout=Counter(r['net_id'] for r in current['connections']);cohort=sorted(n for n,c in fanout.items() if c>=64);selected=sorted(r['connection_id'] for r in current['connections'] if r['net_id'] in cohort);assert len(cohort)==12 and len(selected)==1012;out.mkdir();(out/'checkpoints').mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'search.py').write_text(Path('tools/prepared_budget_pin_candidates.py').read_text());(out/'reference_search.py').write_text(Path('tools/budget_pin_candidates.py').read_text());(out/'delay_cost.py').write_text(Path('tools/buffered_delay_cost.py').read_text());protocol={'input_sha256':inputs,'development_case':'Additional-design transfer of unchanged previously developed rules; all current endpoint fanout at least64, no unseen-family claim','net_ids':cohort,'fanout_threshold':64,'connection_ids':selected,'policy':'ascending CID, all other same-net branches retained; fixed SOURCE physical pin; target original pin or currently unused explicitly full-equivalent pin, other-net saturated channel exclusion, retained-tree incoming edge constraints; minimum lexicographic (marginal span,path span) within original integer delay budget; label cap100000; publish atomic individual replacement only on strict total span improvement','reverse_stop':'unsettled reverse minimum delay above budget','delay_prefilter':'exact shared forward minimum delay; unreachable targets omitted from cost search','native_label_inputs':False,'selector_contract':'explicit equivalent members and dynamic free-pin snapshot; original pin retained; LABEL_LIMIT precludes all-target optimality claim','source_selection':'fanout>=64 ascending net/CID','budget_origin':'current native-validated RouteCast physical path additive buffered RC, not native STA labels','preparation':'external contributions frozen within each net, refreshed between nets; validated immutable arc/background context refreshed per net; sparse retained-tree destination cost overrides'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');g=measured('graph_read',read_rr_graph,files['graph']);engine=measured('search_prepare',BudgetPins,g);model=measured('delay_prepare',BufferedDelayCost,g);e=json.loads(Path(files['endpoints']).read_text());measured('full_physical_audit',audit,g,e,current);ledger=LocalBatchOccupancy(g)
for r in current['connections']:assert measured('ledger_initialization',ledger.update,r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
equivalence={r['cid']:r for r in json.loads(Path(files['equivalence']).read_text())['checks']}
pin_users=defaultdict(set)
for row in current['connections']:
 w=engine.catalog.witness(row['source'],row['sink'],row['physical_edge_ids']);pin_users[row['sink'],w['selected_ipin_ptc']].add(row['connection_id'])
query_candidates=[]
def free_query(context,source,sink,source_ptc,target_ptc,budget,costs,forbidden,max_labels):
 cid=old['connection_id'];occupied={p for (node,p),ids in pin_users.items() if node==sink and ids}
 selected_result=choose(engine,context,source,sink,source_ptc,target_ptc,budget,equivalence[cid]['physical_members'],occupied,equivalence=equivalence[cid]['equivalent'],cost_overrides=costs,blocked_edges=forbidden,max_labels=max_labels,delay_prefilter=True)
 query_candidates.append({'cid':cid,'targets':selected_result['attempts'],'selection_complete':selected_result['selection_complete'],'delay_prefilter':selected_result['delay_prefilter']})
 r=dict(selected_result['best'] if selected_result['best'] is not None else selected_result['attempts'][0]);r['status']=selected_result['status'];r['selection_complete']=selected_result['selection_complete'];r['optimal_over_supplied_free_targets']=selected_result['optimal_over_supplied_free_targets'];return r

original={r['connection_id']:r for r in current['connections']};span={};incoming=defaultdict(list)
for eid,edge in enumerate(g.edges):incoming[edge.sink].append(eid)
for n,node in g.nodes.items():
 loc=dict(node.location);span[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1 if node.type in {'CHANX','CHANY'} else 0
factor=(len(g.nodes)-1)*max(span.values())+1;baseline=scores(g,e,current['node_occupancy']);now=baseline;reports=[]
local_scorer=LocalChannelScores(g)
(out/'local_channel_scores.py').write_text(Path('tools/local_channel_scores.py').read_text());(out/'free_pin_delay_prefilter.py').write_text(Path('tools/free_pin_delay_prefilter.py').read_text());(out/'free_pin_budget_selection.py').write_text(Path('tools/free_pin_budget_selection.py').read_text())
base_costs=measured('base_arc_cost_prepare',lambda:tuple(span[edge.sink]*(factor+1) for edge in g.edges))
def retained_costs(built):
 costs={}
 for node in built:
  for eid in incoming[node]:costs[eid]=span[node]
 return costs
for net in cohort:
 net_cids=[cid for cid in selected if original[cid]['net_id']==net]
 outside={r['connection_id']:r for r in current['connections'] if r['net_id']!=net}
 users,demand=measured('external_background_prepare',net_union,g,current)
 external_demand={n:d-int(n in users[net]) for n,d in demand.items()}
 static_blocked=measured('blocked_channel_scan',lambda:{n for n,node in g.nodes.items() if node.type in {'CHANX','CHANY'} and demand.get(n,0)-int(n in users[net])>=node.capacity})
 prepared=measured('query_context_prepare',engine.prepare,base_costs,model.weights,static_blocked)
 for cid in net_cids:
  rows={r['connection_id']:r for r in current['connections']};old=rows[cid];other=[r for r in current['connections'] if r['net_id']==net and r['connection_id']!=cid];edges={a for r in other for a in r['physical_edge_ids']};built={g.edges[a].sink for a in edges};parents={g.edges[a].sink:a for a in edges};assert len(parents)==len(edges);forbidden={a for n,parent in parents.items() for a in incoming[n] if a!=parent};blocked=static_blocked;w=engine.catalog.witness(old['source'],old['sink'],old['physical_edge_ids']);budget=sum(model.weights[a] for a in original[cid]['physical_edge_ids']);assert not set(old['physical_edge_ids'])&forbidden and all(g.edges[a].sink not in blocked for a in old['physical_edge_ids']);assert sum(model.weights[a] for a in old['physical_edge_ids'])<=budget;costs=measured('arc_cost_copy_and_override',retained_costs,built);t=time.monotonic();r=measured('budget_query',free_query,prepared,old['source'],old['sink'],w['selected_opin_ptc'],w['selected_ipin_ptc'],budget,costs,forbidden,max_labels=100000);q={k:v for k,v in r.items() if k!='path'};q.update(net=net,cid=cid,query_s=time.monotonic()-t,committed=False,before_scores=now);assert r['status']!='UNREACHABLE','original feasible path is an explicit witness'
  if r['status']=='FOUND':
   path=r['path'];assert r['cost']<=sum(costs.get(a,base_costs[a]) for a in old['physical_edge_ids']);assert model.path_delay(old['source'],path)<=model.path_delay(original[cid]['source'],original[cid]['physical_edge_ids']);new={**old,'physical_edge_ids':path,'method':'incremental_budget_free_pin_branch'};gate=measured('whole_net_gate',check,g,current,[new]);assert gate['accepted'];branch=measured('ledger_fork',ledger.fork);update={**{k:new[k] for k in ('connection_id','net_id','source','sink')},'epoch':2,'edge_ids':path};assert measured('atomic_update',branch.update_batch,[update])==Result.COMMITTED;after=measured('local_score',local_scorer.replace_net,now,built|{old['source']}|{g.edges[a].sink for a in old['physical_edge_ids']},built|{old['source']}|{g.edges[a].sink for a in path},external_demand);q['candidate_scores']=after;assert after['predicted_channel_overuse_units']==0 and after['channel_net_span_sum']<=now['channel_net_span_sum']
   if after['channel_net_span_sum']<now['channel_net_span_sum']:
    nw=engine.catalog.witness(new['source'],new['sink'],new['physical_edge_ids']);pin_users[old['sink'],w['selected_ipin_ptc']].remove(cid);pin_users[new['sink'],nw['selected_ipin_ptc']].add(cid);rows[cid]=new;ledger=branch;newrows=list(rows.values());current={'physical_graph_sha256':g.sha256,'connections':newrows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'methods':dict(Counter(x['method'] for x in newrows)),'requested':len(newrows),'completed':len(newrows)};now=after;q['committed']=True
  reports.append(q);(out/'checkpoints'/f'{cid}.json').write_text(json.dumps({'report':q,'target_queries':query_candidates[-1]})+'\n');(out/'progress.json').write_text(json.dumps(reports)+'\n');print(json.dumps({'completed':len(reports),'total':len(selected),'cid':cid,'status':r['status'],'committed':q['committed'],'scores':now}),flush=True)
 assert all(r==outside[r['connection_id']] for r in current['connections'] if r['net_id']!=net)
 (out/f'net_{net}_prediction.json').write_text(json.dumps(current)+'\n')
 assert measured('net_boundary_full_score',scores,g,e,current['node_occupancy'])==now
 print(json.dumps({'net_done':net,'scores':now}),flush=True)
assert all(r==original[r['connection_id']] for r in current['connections'] if r['net_id'] not in cohort)
checked=measured('full_physical_audit',audit,g,e,current);top=measured('final_topology_audit',diagnose,g,current);assert all(not r['internal_multi_incoming_nodes'] and not r['cyclic_union'] and not r['source_has_incoming'] and r['all_nodes_source_reachable'] for r in top['nets']);assert all(sha(p)==h for p,h in inputs.items());(out/'query_candidates.json').write_text(json.dumps(query_candidates)+'\n');(out/'prediction.json').write_text(json.dumps(current)+'\n');result={'baseline_scores':baseline,'final_scores':now,'reports':reports,'physical_audit':checked,'final_topology':top,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'selector_sha256':sha(out/'free_pin_budget_selection.py'),'search_sha256':sha(out/'search.py'),'protocol_sha256':sha(out/'protocol.json'),'prediction_sha256':sha(out/'prediction.json'),'stage_seconds':dict(timings),'stage_calls':dict(calls),'full_wall_s':time.monotonic()-start,'scope':'1012 free-target-pin retained-trunk single-branch budget optimizations on 12 fanout>=64 nets; original exact delay budget, no native label input; no global joint optimum, native QoR or timing parity claim'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'baseline':baseline,'final':now,'committed_connections':sum(r['committed'] for r in reports),'label_limits':sum(r['status']=='LABEL_LIMIT' for r in reports),'full_wall_s':result['full_wall_s']}),flush=True)

reference=Path('experiments/alu4_free_pin_cohort_2026-10-05');old_final=json.loads((reference/'prediction.json').read_text());assert current==old_final
old_reports=json.loads((reference/'receipt.json').read_text())['reports'];fields=('cid','status','cost','delay','selected_ipin_ptc','committed','before_scores','candidate_scores','selection_complete','optimal_over_supplied_free_targets')
assert len(old_reports)==len(reports)
for previous,new in zip(old_reports,reports):
 for field in fields:assert previous.get(field)==new.get(field),(new['cid'],field)
(out/'equivalence.json').write_text(json.dumps({'requests':len(reports),'all_final_prediction_fields_exact':True,'all_report_decisions_exact':True,'reference_prediction_sha256':sha(reference/'prediction.json'),'candidate_prediction_sha256':sha(out/'prediction.json'),'scope':'fresh full optimization and commit gates; identical predictions reuse existing native evidence, not fresh native run'})+'\n')
