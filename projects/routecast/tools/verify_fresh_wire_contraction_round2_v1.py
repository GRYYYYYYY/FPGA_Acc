"""Independent full event replay using original XML physical arcs and Fraction RC."""
import json,xml.etree.ElementTree as ET
from collections import defaultdict,Counter
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read
R=Path(__file__).resolve().parents[1];D=R/'experiments/fresh_wire_contraction_round2_v1_2026-10-08';rp=D/'receipt.json';r=json.loads(rp.read_text());p=json.loads((D/'protocol.json').read_text());assert sha(D/'protocol.json')==r['protocol_sha256'] and all(sha(f)==h for f,h in r['bindings'].items())
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2);meta=json.loads(Path(case['target']).read_text());queries={q['connection_id']:q for q in meta['connections']};assert len(queries)==len(r['events'])==1929 and [e['connection_id'] for e in r['events']]==p['query_order']==sorted(queries)
graph=Path(meta['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,meta['graph_sha256']);ids,classes,switches,digest=read(graph);assert digest==xml.digest;budget=json.loads(Path(case['budget']).read_text());length={}
for n in ET.parse(graph).getroot().find('rr_nodes'):
 if n.get('type') in ('CHANX','CHANY'):
  loc=n.find('loc');length[int(n.get('id'))]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
B=R/'experiments/fresh_wire_contraction_round1_v2_2026-10-08';base=json.loads((B/'receipt.json').read_text())['state'];state={int(cid):tuple(tuple(x) for x in path) for cid,path in base.items()};base_frame=json.loads((B/'verification.json').read_text());delay={x['connection_id']:F(x['delay_seconds']) for x in base_frame['rows']};initial_delay=dict(delay)
def rebuild():
 union=defaultdict(set);parents=defaultdict(dict)
 for cid,path in state.items():
  q=queries[cid];assert path[0]==(q['source'],None) and path[-1][0]==q['sink'] and len({n for n,s in path})==len(path);union[q['net_id']].update(n for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):assert v not in parents[q['net_id']] or parents[q['net_id']][v]==(u,s);parents[q['net_id']][v]=(u,s)
 ledger=Counter(n for ns in union.values() for n in ns);assert all(v<=xml.graph.nodes[n].capacity for n,v in ledger.items());return union,ledger
union,_=rebuild();assert sum(length.get(n,0) for ns in union.values() for n in ns)==r['initial_wire']==11986
commits=0;counts=Counter()
for e in r['events']:
 cid=e['connection_id'];q=queries[cid];net=q['net_id'];assert e['query']==q and F(e['old_delay_seconds'])==delay[cid];limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9;counts[e['status']]+=1
 if e['status']=='RETAIN_ORIGINAL_CERTIFIED_BUDGET_INFEASIBLE':assert cid in (785,1637) and delay[cid]>limit;continue
 assert delay[cid]<=limit;ceiling=(min(limit,delay[cid])*r['scale']);assert e['budget_integer_ceiling']==ceiling.numerator//ceiling.denominator
 answer=e['search'];assert answer['labels_created']<=p['max_labels_per_query']
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
 assert source==q['sink'] and physical_delay*r['scale']==answer['delay']<=e['budget_integer_ceiling'] and physical_delay<=delay[cid]
 new_used=kept|seen;old_wire=sum(length.get(n,0) for n in union[net]);new_wire=sum(length.get(n,0) for n in new_used)
 assert answer['cost']==sum(length.get(n,0) for n in new_used-kept) and e['old_net_wire']==old_wire and e['new_net_wire']==new_wire
 if e['status']=='COMMIT':
  assert new_wire<old_wire and e['new_path']==[list(x) for x in path] and F(e['new_delay_seconds'])==physical_delay;state[cid]=tuple(path);delay[cid]=physical_delay;rebuild();commits+=1
 else:assert e['status']=='RETAIN_FOUND' and new_wire>=old_wire
assert r['state']=={str(cid):[list(x) for x in path] for cid,path in state.items()};union,ledger=rebuild();wire=sum(length.get(n,0) for ns in union.values() for n in ns);assert wire==r['final_wire']<=11986
# Re-audit all final physical paths, including retained and skipped queries.
arc_ids=defaultdict(list)
for eid in range(len(xml.graph.edges)):
 edge=xml.graph.edges[eid];arc_ids[edge.source,edge.sink,edge.switch_id].append(eid)
rows=[];violations=[]
for cid,path in state.items():
 q=queries[cid];assert xml.graph.nodes[q['source']].type=='SOURCE' and xml.graph.nodes[q['sink']].type=='SINK';u=q['source'];nr,nc=classes[ids[u]];value=nr*nc/2;edges=[]
 for dest,s in path[1:]:
  assert len(arc_ids[u,dest,s])==1 and xml.graph.nodes[dest].capacity>0;edges.append(arc_ids[u,dest,s][0]);nr,nc=classes[ids[dest]];sr,td=switches[s];value+=(sr+nr/2)*nc+td;u=dest
 assert value==delay[cid]<=initial_delay[cid];limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9;passed=value<=limit;rows.append(dict(connection_id=cid,delay_seconds=str(value),budget_ns=str(limit*10**9),budget_pass=passed,physical_edge_ids=edges))
 if not passed:violations.append(cid)
assert set(violations)=={785,1637} and commits==sum(e['status']=='COMMIT' for e in r['events']) and all(sha(f)==h for f,h in r['bindings'].items())
bindings={**r['bindings'],str(rp):sha(rp),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/buffered_rc_node_classes.py'):sha(R/'tools/buffered_rc_node_classes.py'),str(R/'tools/immutable_xml_prediction_audit.py'):sha(R/'tools/immutable_xml_prediction_audit.py')}
report=dict(bindings=bindings,all1929_events_and_complete_original_xml_fraction_frame_pass=True,complete_connections=1929,commits=commits,status_counts=dict(counts),initial_wire=11986,final_wire=wire,all_connection_delays_nonincreasing=True,budget_safe_connections=1927,budget_violation_ids=sorted(violations),rows=rows,scope='Independent all-event physical/cost/budget/owner/tree replay and entire final Fraction frame. No optimality claim beyond independently checked physical witnesses; search statuses/counts reported exactly, no native STA/global model or end-to-end gain.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS all1929 events/frame, commits',commits,'wire11986->',wire,'all delays nonincreasing, original two failures retained')
