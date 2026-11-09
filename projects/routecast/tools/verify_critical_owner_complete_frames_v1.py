"""Full original XML/Fraction frames and full-DAG timing certificates for all four transactions."""
import json
from fractions import Fraction as F
from collections import defaultdict,Counter,deque
from pathlib import Path
from pre_route_endpoints import sha
from buffered_rc_node_classes import read
from immutable_xml_prediction_audit import ImmutableXMLAudit
R=Path(__file__).resolve().parents[1];D=R/'experiments/critical_owner_transaction_v1_2026-10-08';rp=D/'receipt.json';vp=D/'verification.json';r=json.loads(rp.read_text());v=json.loads(vp.read_text());assert v['all_four_complete_owner_transactions_replay_pass'] and sha(rp)==v['receipt_sha256'] and all(sha(p)==h for p,h in r['bindings'].items())
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2);ep=json.loads(Path(case['target']).read_text());queries={str(q['connection_id']):q for q in ep['connections']};graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,digest=read(graph);assert digest==xml.digest;budget=json.loads(Path(case['budget']).read_text())
base=json.loads((R/'experiments/budget_occupied_branch_repair_v1_2026-10-08/complete_frame_verification_v2.json').read_text());base_delay={x['connection_id']:F(x['delay_seconds']) for x in base['rows']}
tgp=R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json';mp=R/'experiments/mux_full_timing_rr_2026-10-06/w32.json';ap=R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json';tg=json.loads(tgp.read_text());mapping=json.loads(mp.read_text());allocation=json.loads(ap.read_text());assert allocation['graph_sha256']==sha(tgp)==mapping['timing_graph_sha256'] and allocation['mapping_sha256']==sha(mp)
bindings={**r['bindings'],str(rp):sha(rp),str(vp):sha(vp),str(Path(__file__)):sha(Path(__file__)),**{str(p):sha(p) for p in (tgp,mp,ap)}}
arcs=defaultdict(list)
for eid in range(len(xml.graph.edges)):
 e=xml.graph.edges[eid];arcs[e.source,e.sink,e.switch_id].append(eid)
rows=[]
for ordinal,candidate in enumerate(r['rows']):
 assert candidate['transaction_complete'] and set(candidate['state'])==set(queries);union=defaultdict(set);parents=defaultdict(dict);connection_rows=[];delays={};violations=[]
 for cid,path in candidate['state'].items():
  q=queries[cid];source,sink=q['source'],q['sink'];net=q['net_id'];assert path[0]==[source,None] and path[-1][0]==sink and xml.graph.nodes[source].type=='SOURCE' and xml.graph.nodes[sink].type=='SINK';u=source;used={u};nr,nc=classes[ids[u]];delay=nr*nc/2;edges=[]
  for dst,switch in path[1:]:
   assert dst not in used and xml.graph.nodes[dst].capacity>0;matches=arcs[u,dst,switch];assert len(matches)==1;eid=matches[0];edges.append(eid)
   assert dst not in parents[net] or parents[net][dst]==(u,eid);parents[net][dst]=(u,eid);nr,nc=classes[ids[dst]];sr,td=switches[switch];delay+=(sr+nr/2)*nc+td;used.add(dst);u=dst
  assert xml.graph.nodes[source].capacity>0;union[net].update(used);limit=F(budget['budgets_ns'].get(cid,budget['default_budget_ns']));delays[cid]=delay;passed=delay*10**9<=limit
  row=dict(connection_id=int(cid),delay_seconds=str(delay),budget_ns=str(limit),budget_pass=passed,physical_edge_ids=edges);connection_rows.append(row)
  if not passed:violations.append(int(cid))
 ledger=Counter(n for ns in union.values() for n in ns);assert all(c<=xml.graph.nodes[n].capacity for n,c in ledger.items());assert set(violations)=={785,1637}
 participants=set(candidate['plan']['released_connections'])|{candidate['plan']['critical']}
 for cid,delay in delays.items():
  if int(cid) not in participants:assert delay==base_delay[int(cid)]
 for e in candidate['events']:assert delays[str(e['connection_id'])]*r['scale']==e['delay_integer']
 enabled={eid:e for eid,e in tg['edges'].items() if not e['disabled']};adj=defaultdict(list);ind={int(n):0 for n in tg['nodes']}
 for eid,e in enabled.items():adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
 queue=deque(n for n,d in ind.items() if not d);order=[]
 while queue:
  u=queue.popleft();order.append(u)
  for sink,eid in adj[u]:
   ind[sink]-=1
   if not ind[sink]:queue.append(sink)
 assert len(order)==len(ind);arrival={n:F(0) for n in order};pred={};weights={}
 for u in order:
  for sink,eid in adj[u]:
   delay=delays[str(allocation['edge_connection_ids'][eid])]+F(mapping['external_edges'][eid]['old_local_offset_seconds']) if eid in allocation['edge_connection_ids'] else F(enabled[eid]['max_delay_seconds']);weights[eid]=delay
   value=arrival[u]+delay
   if value>arrival[sink]:arrival[sink]=value;pred[sink]=(u,eid)
 terminals=[int(n) for n,kind in tg['nodes'].items() if kind=='SINK'];critical=max(terminals,key=lambda n:arrival[n]);cpd=arrival[critical]*10**9;path=[];node=critical
 while node in pred:node,eid=pred[node];path.append(eid)
 path.reverse();assert arrival[node]==0;value=F(0)
 for eid in path:
  e=enabled[eid];assert e['source']==node;value+=weights[eid];node=e['sink'];assert value==arrival[node]
 assert node in terminals and value*10**9==cpd and all(arrival[e['sink']]>=arrival[e['source']]+weights[eid] for eid,e in enabled.items())
 report=dict(plan_index=ordinal,plan=candidate['plan'],complete_connections=1929,all_original_xml_physical_tree_capacity_checks_pass=True,budget_safe_connections=1927,budget_violation_ids=sorted(violations),connections=connection_rows,fixed_local_model_cpd_ns=str(cpd),previous_model_cpd_ns='2.873492',strict_model_cpd_improvement=cpd<F('2.873492'),critical_path_edge_ids=path,arrival_seconds={str(n):str(v) for n,v in arrival.items()},edge_delay_seconds={eid:str(v) for eid,v in weights.items()})
 out=D/f'plan{ordinal}_complete_frame.json';out.write_text(json.dumps(report,indent=2)+'\n');bindings[str(out)]=sha(out);rows.append({k:v for k,v in report.items() if k not in ('connections','arrival_seconds','edge_delay_seconds')});print(ordinal,candidate['plan']['critical'],candidate['plan']['order'],'model CPD',float(cpd),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(D/'complete_frames_verification.json').write_text(json.dumps(dict(bindings=bindings,all_four_complete_frames_original_xml_fraction_pass=True,rows=rows,scope='Full physical capacity/shared-tree/Fraction original budget and fixed-old-local full-DAG proof checks; two original infeasible budgets remain. No native/pin/STA/end-to-end gain; no candidate publication.'),indent=2)+'\n')
