import json
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'native_complete_joint_capacity_rc_2026-10-06';receipt=json.loads((out/'receipt.json').read_text());protocol=json.loads((out/'protocol.json').read_text());cohort_path=base/'native_complete_move_queries_2026-10-06/adder_0.json';release_path=base/'native_move_release_contexts_2026-10-06/adder_0.json';assert sha(cohort_path)==protocol['cohort_sha256'] and sha(release_path)==protocol['release_sha256'];assert sha(out/'protocol.json')==receipt['protocol_sha256'];assert all(sha(p)==h for p,h in protocol['implementation_sha256'].items());cohort=json.loads(cohort_path.read_text());release=json.loads(release_path.read_text());graph=Path(next(p for p in cohort['inputs_sha256'] if p.endswith('rr_graph.xml')));audit=ImmutableXMLAudit(graph,protocol['graph_sha256']);ids,classes,switches,digest=read(graph);checked=0;result_rows=[]
for row in receipt['results']:
 p=out/f"pair_{row['pair_index']}.json";assert sha(p)==row['sha256'];data=json.loads(p.read_text());expected={(q['net_id'],q['pin_index']):(q['source'],q['sink']) for q in cohort['moves'][row['pair_index']]['queries']};assert len(data['records'])<=len(expected);successful=0;unions=defaultdict(set);edges=defaultdict(set);roots={}
 for query in data['records']:
  net=query['net_id'];assert expected.pop((net,query['pin_index']))==(query['source'],query['sink']);answer=query['result'];
  if answer['status']!='FOUND':
   assert query is data['records'][-1] and data['failure']==answer['status'];break
  successful+=1;node=query['source'];assert net not in roots or roots[net]==node;roots[net]=node;used={node};unions[net].add(node);r,c=classes[ids[node]];delay=r*c/2
  for eid in answer['physical_edge_ids']:
   edge=audit.graph.edges[eid];assert edge.source==node and edge.sink not in used;node=edge.sink;used.add(node);unions[net].add(node);edges[net].add((edge.source,node,eid));delay+=arc_delay(classes,switches,ids[node],edge.switch_id)
  assert node==query['sink'] and delay==Fraction(answer['delay'],protocol['integer_scale']) and delay<=Fraction(1,10**9);checked+=1
 assert successful==data['completed_connections'];assert data['failure'] is not None or not expected
 for net,arcs in edges.items():
  parents=defaultdict(set)
  for u,v,e in arcs:parents[v].add((u,e))
  assert roots[net] not in parents and all(len(v)==1 for v in parents.values()) and set(parents)==unions[net]-{roots[net]}
 ledger=Counter({int(n):v for n,v in release['moves'][row['pair_index']]['other_demand'].items()});ledger.update(n for used in unions.values() for n in used);violations={n:v-audit.caps[n] for n,v in ledger.items() if v>audit.caps[n]};assert not violations;assert sum(violations.values())==row['overflow_units'];assert violations=={int(n):v for n,v in data['overflow_nodes'].items()};result_rows.append({'pair_index':row['pair_index'],'connections':successful,'required':data['required_connections'],'failure':data['failure'],'overflow_units':sum(violations.values())})
(out/'verification.json').write_text(json.dumps({'connections':checked,'results':result_rows,'graph_sha256':digest,'receipt_sha256':sha(out/'receipt.json'),'scope':'All original XML paths/delays, native pin identity and successful prefix, unique root/parent NET union trees and exact joint capacity replay checked. Capacity checked for successful partial unions; failed greedy routing does not prove infeasibility. These are not publishable native seeds; nonconfigurable closure/full STA not certified.'},indent=2)+'\n');print('verified',checked,'connections;',len(result_rows),'capacity-admitted candidate prefixes')
