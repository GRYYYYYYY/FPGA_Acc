import json
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_frozen_delay_query_2026-10-06';r=json.loads((out/'receipt.json').read_text());parent=root/'experiments/nonzero_rc_ex5p_joint_capacity_2026-10-06/receipt.json';prior=json.loads(parent.read_text());assert r['parent_sha256']==sha(parent) and r['protocol_sha256']==sha(out/'protocol.json') and r['source_sha256']==sha(root/'tools/trial_ex5p_frozen_delay_query.py');ep=json.loads((root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path']);audit=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);unions=defaultdict(set);parents=defaultdict(dict)
for record in prior['records']:
 net=record['net_id'];node=record['source'];unions[net].add(node)
 for eid in record['answer']['physical_edge_ids']:
  edge=audit.graph.edges[eid];assert edge.source==node;node=edge.sink;unions[net].add(node);parents[net][node]=(edge.source,eid)
 assert node==record['sink']
ledger=Counter(n for ns in unions.values() for n in ns);assert dict(ledger)=={int(n):c for n,c in prior['ledger'].items()};q=r['query'];assert q==prior['failure']['query'];other={n:c-int(n in unions[q['net_id']]) for n,c in ledger.items()};other={n:c for n,c in other.items() if c};assert other=={int(n):c for n,c in r['other'].items()};answer=r['answer'];assert answer['status']=='FOUND';node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2;cost=0;conflicts=[];assert other.get(node,0)<audit.caps[node]
for eid in answer['physical_edge_ids']:
 e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);assert other.get(node,0)<audit.caps[node];increment=arc_delay(classes,switches,ids[node],e.switch_id);delay+=increment;cost+=increment*r['scale']*(1+other.get(node,0))
 if node in parents[q['net_id']] and parents[q['net_id']][node]!=(e.source,eid):conflicts.append(node)
assert node==q['sink'] and delay==Fraction(answer['delay'],r['scale'])<=Fraction(1,10**9) and cost==answer['cost'];(out/'verification.json').write_text(json.dumps({'frozen_demand_exactly_replayed':True,'path_delay_ns':float(delay)*1e9,'labels_created':answer['labels_created'],'tree_parent_conflicts':conflicts,'capacity_feasible':True,'receipt_sha256':sha(out/'receipt.json'),'scope':'Same frozen170-prefix query now FOUND with exact XML1ns/capacity/delay-weighted cost witness; no commit, minimum-delay optimality certificate or full1916/native legality/speed claim.'},indent=2)+'\n');print('verified frozen query',float(delay)*1e9,'ns; parent conflicts',len(conflicts))
