"""Independent event-by-event release/accounting/path witness replay."""
import json
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from nonzero_rc_search_context import load
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_delay_objective_repair_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert sha(root/'tools/trial_nonzero_rc_delay_objective_repair.py')==r['source_sha256'] and sha(root/'tools/nonzero_rc_search_context.py')==r['context_sha256'];assert sha(out/'protocol.json')==r['protocol_sha256'];protocol=json.loads((out/'protocol.json').read_text());assert protocol['max_repairs']==4;graph,digest,nodes,f,rc,queries,_=load(root);audit=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);required={(q['net_id'],q['pin_index']):(q['source'],q['sink']) for q in queries};unions=defaultdict(set);ledger=Counter();records={};found=0;releases=0;last_failure=None
for e in r['events']:
 if e['type']=='RELEASE':
  assert last_failure is not None and list((last_failure['net_id'],last_failure['pin_index']))==e['failed_key'];assert releases<4;blockers=set(e['blockers']);other=Counter(ledger)
  for n in unions[last_failure['net_id']]:other[n]-=1
  node=last_failure['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2
  for eid in e['unoccupied_path']:edge=audit.graph.edges[eid];assert edge.source==node and edge.sink not in used;node=edge.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],edge.switch_id)
  assert node==last_failure['sink'] and delay==Fraction(e['unoccupied_delay_integer'],r['scale'])<=Fraction(1,10**9);expected=set()
  for n in used:
   if other[n]>=audit.caps[n]:expected.update(net for net,union in unions.items() if net!=last_failure['net_id'] and n in union)
  assert expected==blockers and {str(net):sorted(unions[net]) for net in blockers}==e['released_nodes'];assert sorted([list(k) for k in records if k[0] in blockers])==e['released_records']
  for net in blockers:
   for n in unions[net]:ledger[n]-=1;assert ledger[n]>=0
   del unions[net]
  records={k:v for k,v in records.items() if k[0] not in blockers};releases+=1;continue
 assert e['type']=='QUERY';key=(e['net_id'],e['pin_index']);assert required[key]==(e['source'],e['sink']) and key not in records;answer=e['result']
 if answer['status']!='FOUND':last_failure=e;continue
 other=Counter(ledger)
 for n in unions[e['net_id']]:other[n]-=1
 node=e['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2
 for eid in answer['physical_edge_ids']:edge=audit.graph.edges[eid];assert edge.source==node and edge.sink not in used;node=edge.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],edge.switch_id)
 assert node==e['sink'] and delay==Fraction(answer['delay'],r['scale'])<=Fraction(1,10**9);assert all(other[n]<audit.caps[n] for n in used);assert answer['cost']==sum((other[audit.graph.edges[eid].sink]+1)*arc_delay(classes,switches,ids[audit.graph.edges[eid].sink],audit.graph.edges[eid].switch_id)*r['scale'] for eid in answer['physical_edge_ids']);ledger.update(used-unions[e['net_id']]);unions[e['net_id']].update(used);records[key]={k:v for k,v in e.items() if k!='type'};found+=1
assert records=={(q['net_id'],q['pin_index']):q for q in r['records']};assert len(records)==59 and releases==r['repairs']==4 and r['status']=='INCOMPLETE_NOT_PUBLISHABLE' and r['terminal']=='UNREACHABLE';assert all(v<=audit.caps[n] for n,v in ledger.items());parents=defaultdict(set)
for q in records.values():
 for eid in q['result']['physical_edge_ids']:edge=audit.graph.edges[eid];parents[(q['net_id'],edge.sink)].add((edge.source,eid))
assert all(len(p)==1 for p in parents.values()) and not r['overflow_nodes'] and not r['multi_parent_nodes'];(out/'verification.json').write_text(json.dumps({'completed_connections':59,'required_connections':69,'releases':releases,'all_found_witnesses_checked_including_released':found,'overflow_units':0,'multi_parent_nodes':0,'receipt_sha256':sha(out/'receipt.json'),'scope':'Exact original XML event replay validates every successful query, resource-derived blocker release, ledger accounting, fixed1ns delay, exact delay-increment demand cost and retained final tree parents. Four-attempt ceiling reached; incomplete predicted seed is forbidden. No global infeasibility/native residual/closure/FULL/STA claim.'},indent=2)+'\n');print('verified59/69, four releases,',found,'successful query witnesses')
