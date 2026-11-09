"""Independent originalXML endpoints/path/delay/cost and diagnostic union accounting."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_ex5p_independent_prediction_2026-10-06';r=json.loads((out/'receipt.json').read_text());protocol=json.loads((out/'protocol.json').read_text());ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json';endpoints=json.loads(ep.read_text());assert protocol['endpoint_sha256']==sha(ep) and r['protocol_sha256']==sha(out/'protocol.json') and r['source_sha256']==sha(root/'tools/trial_nonzero_rc_ex5p_independent_prediction.py');assert protocol['context_source_sha256']==sha(root/'tools/nonzero_rc_endpoint_context.py') and protocol['native_library_sha256']==sha(root/'build/rc_capacity_native_2026-10-06/search.so');assert all(sha(v['path'])==v['sha256'] for v in endpoints['inputs'].values());graph=Path(endpoints['inputs']['graph']['path']);assert r['graph_sha256']==endpoints['graph_sha256'];audit=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);expected={q['connection_id']:q for q in endpoints['connections']};seen=set();checked=0;owners=defaultdict(set);incoming=defaultdict(set);statuses=Counter()
for row in r['records']:
 cid=row['connection_id'];assert cid in expected and cid not in seen;seen.add(cid);q=expected[cid];assert all(row[k]==value for k,value in q.items());answer=row['answer'];statuses[answer['status']]+=1
 if answer['status']!='FOUND':assert answer['status']=='LABEL_LIMIT' and answer['physical_edge_ids'] is None and answer['delay'] is None;continue
 node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2;assert audit.caps[node]>0
 for eid in answer['physical_edge_ids']:
  e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);assert audit.caps[node]>0;delay+=arc_delay(classes,switches,ids[node],e.switch_id);incoming[q['net_id'],node].add((e.source,eid))
 assert node==q['sink'] and delay==Fraction(answer['delay'],r['scale'])<=Fraction(1,10**9) and answer['cost']==len(answer['physical_edge_ids']);checked+=1
 for n in used:owners[n].add(q['net_id'])
assert seen==set(expected) and len(seen)==r['connections']==1916 and dict(statuses)==r['statuses'];overflow=sum(max(0,len(nets)-audit.caps[n]) for n,nets in owners.items());multi=sum(len(v)>1 for v in incoming.values());(out/'verification.json').write_text(json.dumps({'connections':1916,'found_paths_checked':checked,'label_limit_queries':statuses['LABEL_LIMIT'],'diagnostic_union_overflow_units':overflow,'diagnostic_multi_parent_NET_nodes':multi,'receipt_sha256':sha(out/'receipt.json'),'scope':'All declared pre-route endpoints matched; everyFOUND originalXML simplepath/exact1ns/capacity/unitcost independently audited. LABEL_LIMIT is not unreachable proof. Independent queries have empty demand and their aggregate is incomplete/nonpublishable, not joint nativeFULL/STA or net runtime benefit.'},indent=2)+'\n');print('verified',checked,'paths; label limits',statuses['LABEL_LIMIT'],'diagnostic overflow',overflow,'multiparents',multi)
