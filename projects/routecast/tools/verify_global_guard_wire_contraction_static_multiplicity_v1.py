"""Independent full event replay using original XML physical arcs and Fraction RC."""
import json,xml.etree.ElementTree as ET
from collections import defaultdict,Counter
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read
from exact_integer_global_timing_v2 import ExactGlobalTiming
R=Path(__file__).resolve().parents[1];D=R/'experiments/global_guard_wire_contraction_static_multiplicity_v1_2026-10-08';rp=D/'receipt.json';r=json.loads(rp.read_text());p=json.loads((D/'protocol.json').read_text());assert sha(D/'protocol.json')==r['protocol_sha256'] and all(sha(f)==h for f,h in r['bindings'].items())
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2);meta=json.loads(Path(case['target']).read_text());queries={q['connection_id']:q for q in meta['connections']};assert len(queries)==len(r['events'])==1929 and [e['connection_id'] for e in r['events']]==p['query_order']==sorted(queries)
graph=Path(meta['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,meta['graph_sha256']);ids,classes,switches,digest=read(graph);assert digest==xml.digest;budget=json.loads(Path(case['budget']).read_text());length={}
for n in ET.parse(graph).getroot().find('rr_nodes'):
 if n.get('type') in ('CHANX','CHANY'):
  loc=n.find('loc');length[int(n.get('id'))]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
B=R/'experiments/complete_wire_contraction_v2_2026-10-08';base=json.loads((B/'receipt.json').read_text())['state'];state={int(cid):tuple(tuple(x) for x in path) for cid,path in base.items()};base_frame=json.loads((B/'verification_v3.json').read_text());delay={x['connection_id']:F(x['delay_seconds']) for x in base_frame['rows']};initial_delay=dict(delay)
def rebuild():
 union=defaultdict(set);parents=defaultdict(dict)
 for cid,path in state.items():
  q=queries[cid];assert path[0]==(q['source'],None) and path[-1][0]==q['sink'] and len({n for n,s in path})==len(path);union[q['net_id']].update(n for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):assert v not in parents[q['net_id']] or parents[q['net_id']][v]==(u,s);parents[q['net_id']][v]=(u,s)
 ledger=Counter(n for ns in union.values() for n in ns);assert all(v<=xml.graph.nodes[n].capacity for n,v in ledger.items());return union,ledger
union,_=rebuild();assert sum(length.get(n,0) for ns in union.values() for n in ns)==r['initial_wire']==11971

# Independent dynamic timing reconstruction, with attaining predecessor chain.
from collections import deque
tg=json.loads((R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json').read_text());mapping=json.loads((R/'experiments/mux_full_timing_rr_2026-10-06/w32.json').read_text());allocation=json.loads((R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json').read_text())
assert allocation['graph_sha256']==sha(R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json')==mapping['timing_graph_sha256'] and allocation['mapping_sha256']==sha(R/'experiments/mux_full_timing_rr_2026-10-06/w32.json')
edges={eid:e for eid,e in tg['edges'].items() if not e['disabled']};adj=defaultdict(list);degree={int(n):0 for n in tg['nodes']};groups=defaultdict(set)
for eid,e in edges.items():
 adj[e['source']].append((e['sink'],eid));degree[e['sink']]+=1
 if eid in allocation['edge_connection_ids']:groups[allocation['edge_connection_ids'][eid]].add(eid)
queue=deque(n for n,v in degree.items() if v==0);order=[]
while queue:
 u=queue.popleft();order.append(u)
 for v,eid in adj[u]:
  degree[v]-=1
  if degree[v]==0:queue.append(v)
assert len(order)==len(degree);sinks={int(n) for n,k in tg['nodes'].items() if k=='SINK'};target=F('2.87238')/10**9;multiplicity={};timing_checks=0
for cid in queries:
 counts={n:0 for n in order}
 for u in order:
  for v,eid in adj[u]:counts[v]=max(counts[v],counts[u]+int(eid in groups[cid]))
 multiplicity[cid]=max(counts[n] for n in sinks)
integer_model=ExactGlobalTiming(tg,mapping,allocation,r['scale'],target,delay)
def certify_timing():
 global timing_checks
 weights={eid:delay[allocation['edge_connection_ids'][eid]]+F(mapping['external_edges'][eid]['old_local_offset_seconds']) if eid in allocation['edge_connection_ids'] else F(e['max_delay_seconds']) for eid,e in edges.items()}
 forward={n:F(0) for n in order};pred={}
 for u in order:
  for v,eid in adj[u]:
   value=forward[u]+weights[eid]
   if value>forward[v]:forward[v]=value;pred[v]=eid
 back={n:F(0) if n in sinks else None for n in order}
 for u in reversed(order):
  candidates=[weights[eid]+back[v] for v,eid in adj[u] if back[v] is not None]
  if back[u] is not None:candidates.append(back[u])
  if candidates:back[u]=max(candidates)
 for eid,e in edges.items():
  assert forward[e['sink']]>=forward[e['source']]+weights[eid]
  if back[e['sink']] is not None:assert back[e['source']]>=weights[eid]+back[e['sink']]
  timing_checks+=1
 integer_model.delays={cid:integer_model.encode(value) for cid,value in delay.items()};integer_model.recompute()
 assert all(F(value,integer_model.scale)==weights[eid] for eid,value in integer_model.weights.items())
 assert all(F(value,integer_model.scale)==forward[n] for n,value in integer_model.forward.items())
 assert all((None if value is None else F(value,integer_model.scale))==back[n] for n,value in integer_model.back.items())
 end=max(sinks,key=lambda n:forward[n]);cpd=forward[end];total=F(0);critical=[]
 while end in pred:
  eid=pred[end];critical.append(eid);total+=weights[eid];end=edges[eid]['source']
 assert total==cpd and forward[end]==0 and cpd<=target
 return weights,forward,back,cpd,critical[::-1]
weights,forward,back,cpd,critical=certify_timing()

commits=0;counts=Counter()
for e in r['events']:
 cid=e['connection_id'];q=queries[cid];net=q['net_id'];assert e['query']==q and F(e['old_delay_seconds'])==delay[cid];limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9;counts[e['status']]+=1
 if e['status']=='RETAIN_ORIGINAL_CERTIFIED_BUDGET_INFEASIBLE':assert cid in (785,1637) and delay[cid]>limit;continue
 assert delay[cid]<=limit
 relevant=[eid for eid in groups[cid] if back[edges[eid]['sink']] is not None];k=multiplicity[cid]
 slack=min(target-forward[edges[eid]['source']]-weights[eid]-back[edges[eid]['sink']] for eid in relevant) if relevant else None
 upper=min(limit,delay[cid]+slack/k) if relevant else limit
 assert (not relevant and k==0) or (k>0 and slack>=0 and k*(upper-delay[cid])<=slack)
 assert integer_model.safe_upper(cid,limit)==(upper,k,slack)
 assert F(e['global_upper_seconds'])==upper and F(e['model_cpd_before_ns'])==cpd*10**9 and e['max_occurrences']==k and e['min_edge_slack_seconds']==(str(slack) if slack is not None else None)
 ceiling=upper*r['scale'];assert e['budget_integer_ceiling']==ceiling.numerator//ceiling.denominator
 bound_kept={n for other,path in state.items() if other!=cid and queries[other]['net_id']==net for n,s in path};bound_union={n for other,path in state.items() if queries[other]['net_id']==net for n,s in path};strict_bound=sum(length.get(n,0) for n in bound_union-bound_kept)
 assert strict_bound==e['strict_wire_cost_bound']>=0
 answer=e['search'];assert answer['labels_created']<=p['max_labels_per_query']
 if strict_bound==0:assert answer['status']=='NO_STRICT_IMPROVEMENT' and answer['labels_created']==answer['labels_expanded']==answer['examined_edges']==0
 if answer['status']=='FOUND':assert answer['cost']<strict_bound
 if answer['status']!='FOUND':assert e['status']=='RETAIN_'+answer['status'] and answer['physical_edge_ids'] is None;continue
 union,ledger=rebuild();outside=ledger.copy();outside.subtract(union[net]);kept=set();fixed={}
 for other,path in state.items():
  if other!=cid and queries[other]['net_id']==net:
   kept.update(n for n,s in path)
   for (u,_),(v,s) in zip(path,path[1:]):assert v not in fixed or fixed[v]==(u,s);fixed[v]=(u,s)
 source=q['source'];nr,nc=classes[ids[source]];physical_delay=nr*nc/2;path=[(source,None)];seen={source}
 for eid in answer['physical_edge_ids']:
  edge=xml.graph.edges[eid];assert edge.source==source;dest=edge.sink;s=edge.switch_id
  assert dest not in seen and outside[dest]<xml.graph.nodes[dest].capacity and (dest not in fixed or fixed[dest]==(source,s));nr,nc=classes[ids[dest]];sr,td=switches[s];physical_delay+=(sr+nr/2)*nc+td;path.append((dest,s));seen.add(dest);source=dest
 assert source==q['sink'] and physical_delay*r['scale']==answer['delay']<=e['budget_integer_ceiling'] and physical_delay<=upper<=limit
 new_used=kept|seen;old_wire=sum(length.get(n,0) for n in union[net]);new_wire=sum(length.get(n,0) for n in new_used)
 assert answer['cost']==sum(length.get(n,0) for n in new_used-kept) and e['old_net_wire']==old_wire and e['new_net_wire']==new_wire
 if e['status']=='COMMIT':
  assert new_wire<old_wire and e['new_path']==[list(x) for x in path] and F(e['new_delay_seconds'])==physical_delay;state[cid]=tuple(path);delay[cid]=physical_delay;rebuild();commits+=1;weights,forward,back,cpd,critical=certify_timing();assert F(e['model_cpd_after_ns'])==cpd*10**9
 else:assert e['status']=='RETAIN_FOUND' and new_wire>=old_wire
assert r['state']=={str(cid):[list(x) for x in path] for cid,path in state.items()};union,ledger=rebuild();wire=sum(length.get(n,0) for ns in union.values() for n in ns);assert wire==r['final_wire']<=11971
# Re-audit all final physical paths, including retained and skipped queries.
arc_ids=defaultdict(list)
for eid in range(len(xml.graph.edges)):
 edge=xml.graph.edges[eid];arc_ids[edge.source,edge.sink,edge.switch_id].append(eid)
rows=[];violations=[]
for cid,path in state.items():
 q=queries[cid];assert xml.graph.nodes[q['source']].type=='SOURCE' and xml.graph.nodes[q['sink']].type=='SINK';u=q['source'];nr,nc=classes[ids[u]];value=nr*nc/2;edges=[]
 for dest,s in path[1:]:
  assert len(arc_ids[u,dest,s])==1 and xml.graph.nodes[dest].capacity>0;edges.append(arc_ids[u,dest,s][0]);nr,nc=classes[ids[dest]];sr,td=switches[s];value+=(sr+nr/2)*nc+td;u=dest
 assert value==delay[cid];limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9;passed=value<=limit;rows.append(dict(connection_id=cid,delay_seconds=str(value),budget_ns=str(limit*10**9),budget_pass=passed,physical_edge_ids=edges))
 if not passed:violations.append(cid)
assert set(violations)=={785,1637} and commits==sum(e['status']=='COMMIT' for e in r['events']) and all(sha(f)==h for f,h in r['bindings'].items())
bindings={**r['bindings'],str(rp):sha(rp),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/buffered_rc_node_classes.py'):sha(R/'tools/buffered_rc_node_classes.py'),str(R/'tools/immutable_xml_prediction_audit.py'):sha(R/'tools/immutable_xml_prediction_audit.py')}
report=dict(bindings=bindings,all1929_events_and_complete_original_xml_fraction_frame_pass=True,complete_connections=1929,commits=commits,status_counts=dict(counts),initial_wire=11971,final_wire=wire,all_dynamic_model_guards_pass=True,all114_integer_timing_full_weights_arrivals_suffixes_equal_independent_fraction=True,integer_timing_lattice_scale=integer_model.scale,model_cpd_ns=str(cpd*10**9),target_model_cpd_ns="2.87238",timing_edge_inequality_checks=timing_checks,critical_timing_edge_ids=critical,delay_increase_connections=sum(delay[c]>initial_delay[c] for c in delay),budget_safe_connections=1927,budget_violation_ids=sorted(violations),rows=rows,scope='Independent all-event physical/cost/budget/owner/tree replay and entire final Fraction frame. Strict cost-bound identity independently reconstructed for every eligible query; nonnegative objective excludes all pruned labels from strict improvement. No independent optimality/infeasibility claim for search exhaustion or label limits beyond physical witnesses; search statuses/counts reported exactly, dynamic fixed-local DAG guard certified; no native STA or end-to-end gain.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS all1929 events/frame/dynamic timing, commits',commits,'wire',wire,'model CPD ns',str(cpd*10**9),flush=True)
