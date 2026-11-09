"""Independent complete-state original XML physical and exact Fraction budget audit."""
import json
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from buffered_rc_node_classes import read
from immutable_xml_prediction_audit import ImmutableXMLAudit
R=Path(__file__).resolve().parents[1];D=R/'experiments/critical_branch_occupied_repair_v1_2026-10-08';rp=D/'receipt.json';vp=D/'verification.json';r=json.loads(rp.read_text());v=json.loads(vp.read_text())
assert sha(rp)==v['receipt_sha256'] and v['all_sequential_constrained_replay_pass']
assert all(sha(p)==h for p,h in r['bindings'].items())
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
ep=json.loads(Path(case['target']).read_text());graph=Path(ep['inputs']['graph']['path']);budget_path=Path(case['budget']);b=json.loads(budget_path.read_text());xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,digest=read(graph);assert digest==xml.digest
bindings={**r['bindings'],str(rp):sha(rp),str(vp):sha(vp),str(Path(case['target'])):sha(case['target']),str(budget_path):sha(budget_path),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/buffered_rc_node_classes.py'):sha(R/'tools/buffered_rc_node_classes.py'),str(R/'tools/immutable_xml_prediction_audit.py'):sha(R/'tools/immutable_xml_prediction_audit.py')}
arcs=defaultdict(list)
for eid in range(len(xml.graph.edges)):
 e=xml.graph.edges[eid];arcs[e.source,e.sink,e.switch_id].append(eid)
queries={str(q['connection_id']):q for q in ep['connections']};assert set(r['state'])==set(queries) and len(queries)==1929
unions=defaultdict(set);parents=defaultdict(dict);rows=[];failures=[]
for cid,path in r['state'].items():
 q=queries[cid];source,sink=q['source'],q['sink'];net=q['net_id'];assert path[0]==[source,None] and path[-1][0]==sink
 assert xml.graph.nodes[source].type=='SOURCE' and xml.graph.nodes[sink].type=='SINK'
 u=source;used={u};nr,nc=classes[ids[u]];delay=nr*nc/2;edges=[]
 for dst,switch in path[1:]:
  assert dst not in used and xml.graph.nodes[dst].capacity>0
  candidates=arcs[u,dst,switch];assert len(candidates)==1;eid=candidates[0];edges.append(eid)
  assert dst not in parents[net] or parents[net][dst]==(u,eid);parents[net][dst]=(u,eid)
  nr,nc=classes[ids[dst]];sr,td=switches[switch];delay+=(sr+nr/2)*nc+td;used.add(dst);u=dst
 assert u==sink and xml.graph.nodes[source].capacity>0;unions[net].update(used)
 limit=Fraction(b['budgets_ns'].get(cid,b['default_budget_ns']));row=dict(connection_id=int(cid),delay_seconds=str(delay),budget_ns=str(limit),budget_pass=delay*10**9<=limit,physical_edge_ids=edges);rows.append(row)
 if not row['budget_pass']:failures.append(row)
ledger=Counter(n for nodes in unions.values() for n in nodes);assert all(v<=xml.graph.nodes[n].capacity for n,v in ledger.items())
old=json.loads((R/'experiments/budget_occupied_branch_repair_v1_2026-10-08/complete_frame_verification_v2.json').read_text());oldby={x['connection_id']:x for x in old['rows']};events={e['connection_id']:e for e in r['events']}
for row in rows:
 cid=row['connection_id']
 if cid not in events:assert row['delay_seconds']==oldby[cid]['delay_seconds'] and row['budget_pass']==oldby[cid]['budget_pass']
 else:assert row['budget_pass'] and Fraction(row['delay_seconds'])*r['scale']==events[cid]['delay_integer']
assert {x['connection_id'] for x in failures}=={785,1637}
assert all(sha(p)==h for p,h in bindings.items())
report=dict(bindings=bindings,complete_connections=1929,all_original_xml_physical_tree_capacity_checks_pass=True,all_budgets_pass=False,budget_safe_connections=1927,violations=failures,all_three_critical_connections_budget_safe=True,all_other_connection_delays_unchanged=True,rows=rows,scope='Complete exact buffered XML Fraction model frame; two original certified budget-infeasible queries remain, no native pin/nonconfigurable/STA acceptance or performance proof.')
with (D/'complete_frame_verification_v1.json').open('x') as out:out.write(json.dumps(report,indent=2)+'\n')
print('PASS complete physical frame; 1927 budget safe; failures 785,1637; all other delays unchanged')
