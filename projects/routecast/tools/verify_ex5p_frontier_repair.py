"""Independent wholeNET release, query ordering, paths/cost/capacity/parent replay."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_frontier_repair_2026-10-06';r=json.loads((out/'receipt.json').read_text());parent=root/'experiments/nonzero_rc_ex5p_joint_delay_2026-10-06';prior=json.loads((parent/'receipt.json').read_text());proof=json.loads((parent/'verification.json').read_text());assert r['parent_sha256']==sha(parent/'receipt.json') and proof['receipt_sha256']==sha(parent/'receipt.json') and r['protocol_sha256']==sha(out/'protocol.json') and r['source_sha256']==sha(root/'tools/trial_ex5p_frontier_repair.py');ep=json.loads((root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json').read_text());assert all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values());audit=ImmutableXMLAudit(Path(ep['inputs']['graph']['path']),r['graph_sha256']);ids,classes,switches,_=read(Path(ep['inputs']['graph']['path']));unions=defaultdict(set);parents=defaultdict(dict);ledger=Counter();records={};witnesses=0

def decode(q,answer,other=None):
 global witnesses
 assert answer['status']=='FOUND';node=q['source'];used={node};incoming={};res,cap=classes[ids[node]];delay=res*cap/2;cost=0
 if other is not None:assert other.get(node,0)<audit.caps[node]
 for eid in answer['physical_edge_ids']:
  e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);increment=arc_delay(classes,switches,ids[node],e.switch_id);delay+=increment;incoming[node]=(e.source,eid)
  if other is not None:assert other.get(node,0)<audit.caps[node];cost+=increment*r['scale']*(1+other.get(node,0))
 assert node==q['sink'] and delay==Fraction(answer['delay'],r['scale'])<=Fraction(1,10**9)
 if other is not None:assert cost==answer['cost']
 witnesses+=1;return used,incoming

def accept(q,record,used,incoming):
 net=q['net_id'];assert q['connection_id'] not in records and all(n not in parents[net] or parents[net][n]==p for n,p in incoming.items());parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);records[q['connection_id']]=record
for q in prior['records']:
 used,incoming=decode(q,q['answer']);accept(q,q,used,incoming)
assert dict(ledger)=={int(n):c for n,c in prior['ledger'].items()};failed=prior['failure']['query'];owners={n:sorted(net for net,used in unions.items() if n in used and net!=failed['net_id']) for n in proof['blocked_frontier_nodes']};blockers=sorted({net for nets in owners.values() for net in nets});release=r['release'];assert owners=={int(n):nets for n,nets in release['frontier_owners'].items()} and blockers==release['blocker_NETs'];removed=[q['connection_id'] for q in prior['records'] if q['net_id'] in blockers];assert removed==release['removed_connection_ids'];assert {net:sorted(unions[net]) for net in blockers}=={int(net):ns for net,ns in release['released_unions'].items()}
for net in blockers:ledger.subtract(unions[net]);del unions[net];del parents[net]
ledger=+ledger
for cid in removed:del records[cid]
queries=ep['connections'];queue=[failed]+[q for q in sorted(queries,key=lambda q:(q['net_id'],q['connection_id'])) if q['net_id'] in blockers]+[q for q in queries if q['connection_id']>=failed['connection_id'] and q['connection_id']!=failed['connection_id'] and q['net_id'] not in blockers]
for index,attempt in enumerate(r['attempts']):
 q=queue[index];assert attempt['query']==q;net=q['net_id'];other={n:c-int(n in unions[net]) for n,c in ledger.items()};other={n:c for n,c in other.items() if c};answer=attempt['answer']
 if index==len(r['attempts'])-1:
  assert answer['status']=='UNREACHABLE' and r['failure']=={'query':q,'status':'UNREACHABLE'};failed_query=q;failed_other=other;break
 used,incoming=decode(q,answer,other);accept(q,{**q,'mode':'NATIVE_DELAY_COST','answer':answer},used,incoming)
assert [records[k] for k in sorted(records)]==r['records'] and dict(ledger)=={int(n):c for n,c in r['ledger'].items()};assert len(records)==r['completed_connections']==1793 and r['required_connections']==1916 and r['status']=='INCOMPLETE_NOT_PUBLISHABLE' and all(c<=audit.caps[n] for n,c in ledger.items())
adjacency=defaultdict(list)
for eid in range(len(audit.graph.edges)):e=audit.graph.edges[eid];adjacency[e.source].append(e.sink)
reachable=set();pending=[]
if failed_other.get(failed_query['source'],0)<audit.caps[failed_query['source']]:reachable.add(failed_query['source']);pending.append(failed_query['source'])
while pending:
 for n in adjacency[pending.pop()]:
  if n not in reachable and failed_other.get(n,0)<audit.caps[n]:reachable.add(n);pending.append(n)
disconnected=failed_query['sink'] not in reachable;frontier=sorted({n for u in reachable for n in adjacency[u] if n not in reachable});assert all(failed_other.get(n,0)>=audit.caps[n] for n in frontier)
(out/'verification.json').write_text(json.dumps({'retained_paths':1793,'successful_path_witnesses_replayed':witnesses,'whole_NETs_released':blockers,'removed_connections':len(removed),'reroute_attempts':len(r['attempts']),'overflow_units':0,'multi_parent_nodes':0,'failure_not_committed':True,'failed_state_capacity_disconnected':disconnected,'reachable_nodes':len(reachable),'blocked_frontier_nodes':frontier,'receipt_sha256':sha(out/'receipt.json'),'scope':'OriginalXML/1ns/wholeNET release/requeued queries/cost/ledger/parents independently replayed. Reachability proof is frozen capacity state only; if connected, nativeUNREACHABLE lacks independent delay lower-bound proof. Incomplete prefix never nativeFULL/published/speed claim.'},indent=2)+'\n');print('verified1793 retained paths; release',blockers,'new disconnection',disconnected,'reachable',len(reachable),'frontier',len(frontier))
