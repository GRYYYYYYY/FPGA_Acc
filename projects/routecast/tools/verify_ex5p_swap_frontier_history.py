"""Independent XML path, history, queue, cut and wholeNET mutation event replay."""
import json
from pathlib import Path
from collections import Counter,defaultdict,deque
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_swap_frontier_history_2026-10-06';r=json.loads((out/'receipt.json').read_text());parent=root/'experiments/ex5p_swap_incremental_2026-10-06';prior=json.loads((parent/'receipt.json').read_text());verified=json.loads((parent/'verification.json').read_text());assert verified['receipt_sha256']==sha(parent/'receipt.json') and r['parent_sha256']==sha(parent/'receipt.json') and r['protocol_sha256']==sha(out/'protocol.json') and r['source_sha256']==sha(root/'tools/trial_ex5p_swap_frontier_history.py');ep=json.loads((root/'experiments/ex5p_placement_swap_2026-10-06/endpoints.json').read_text());assert all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values());audit=ImmutableXMLAudit(Path(ep['inputs']['graph']['path']),r['graph_sha256']);ids,classes,switches,_=read(Path(ep['inputs']['graph']['path']));adj=defaultdict(list)
for eid in range(len(audit.graph.edges)):e=audit.graph.edges[eid];adj[e.source].append(e.sink)
unions=defaultdict(set);parents=defaultdict(dict);ledger=Counter();records={};history=Counter({int(n):c for n,c in prior['history'].items()});witnesses=0

def path(q,answer,other=None):
 global witnesses
 assert answer['status']=='FOUND';node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2;cost=0;incoming={}
 if other is not None:assert other.get(node,0)<audit.caps[node]
 for eid in answer['physical_edge_ids']:
  e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);increment=arc_delay(classes,switches,ids[node],e.switch_id);delay+=increment;incoming[node]=(e.source,eid)
  if other is not None:assert other.get(node,0)<audit.caps[node];cost+=increment*r['scale']*(1+history[node])*(1+other.get(node,0))
 assert node==q['sink'] and delay==Fraction(answer['delay'],r['scale'])<=Fraction(1,10**9)
 if other is not None:assert cost==answer['cost']
 witnesses+=1;return used,incoming

def accept(q,record,used,incoming):
 net=q['net_id'];assert q['connection_id'] not in records and all(n not in parents[net] or parents[net][n]==p for n,p in incoming.items());parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);records[q['connection_id']]=record

def reach(q,other):
 found=set();stack=[]
 if other.get(q['source'],0)<audit.caps[q['source']]:found.add(q['source']);stack.append(q['source'])
 while stack:
  for n in adj[stack.pop()]:
   if n not in found and other.get(n,0)<audit.caps[n]:found.add(n);stack.append(n)
 return found
for q in prior['records']:used,incoming=path(q,q['answer']);accept(q,q,used,incoming)
assert dict(ledger)=={int(n):c for n,c in prior['ledger'].items()};failed=prior['failure']['query'];queries=ep['connections'];pending=deque([failed]+[q for q in queries if q['connection_id'] not in records and q['connection_id']!=failed['connection_id']]);repairs=0;last=None;releases=[]
for event in r['events']:
 if event['type']=='QUERY':
  q=pending.popleft();assert q==event['query'];net=q['net_id'];other={n:c-int(n in unions[net]) for n,c in ledger.items()};other={n:c for n,c in other.items() if c};answer=event['answer'];last=(q,other,answer)
  if answer['status']=='FOUND':
   used,incoming=path(q,answer,other);assert event['committed'];accept(q,{**q,'mode':'NATIVE_HISTORY_DELAY_COST','answer':answer},used,incoming)
  else:assert not event['committed'] and answer['status']=='UNREACHABLE'
 else:
  assert event['type']=='RELEASE' and last is not None and repairs<4;q,other,answer=last;assert answer['status']=='UNREACHABLE' and event['failed_query']==q;reachable=reach(q,other);assert q['sink'] not in reachable and sorted(reachable)==event['reachable'];frontier=sorted({n for u in reachable for n in adj[u] if n not in reachable}) if reachable else [q['source']];assert frontier==event['frontier'] and all(other.get(n,0)>=audit.caps[n] for n in frontier);owners={n:sorted(k for k,ns in unions.items() if k!=q['net_id'] and n in ns) for n in frontier};blockers=sorted({k for ks in owners.values() for k in ks});assert owners=={int(n):ks for n,ks in event['owners'].items()} and blockers==event['blocker_NETs'];removed=sorted(cid for cid,row in records.items() if row['net_id'] in blockers);assert removed==event['removed_connection_ids'];assert {k:sorted(unions[k]) for k in blockers}=={int(k):ns for k,ns in event['released_unions'].items()}
  for k in blockers:ledger.subtract(unions[k]);del unions[k];del parents[k]
  ledger=+ledger
  for cid in removed:del records[cid]
  history.update(frontier);assert dict(history)=={int(n):c for n,c in event['history_after'].items()};pending=deque([q]+[x for x in sorted(queries,key=lambda x:(x['net_id'],x['connection_id'])) if x['net_id'] in blockers]+[x for x in pending if x['net_id'] not in blockers]);repairs+=1;releases.append({'NETs':blockers,'removed':len(removed),'frontier':len(frontier)})
assert repairs==r['repairs']<=4 and [records[k] for k in sorted(records)]==r['records'] and dict(ledger)=={int(n):c for n,c in r['ledger'].items()} and dict(history)=={int(n):c for n,c in r['history'].items()}
assert len(records)==r['completed_connections'] and r['required_connections']==1916
if r['failure'] is None:
 assert not pending and len(records)==1916 and r['status']=='COMPLETE_DIAGNOSTIC'
else:
 q,other,answer=last;assert r['failure']['query']==q and r['status']=='INCOMPLETE_NOT_PUBLISHABLE'
 if r['failure']['status']=='CONNECTED_BUDGET_OR_SEARCH_FAILURE':assert q['sink'] in reach(q,other) and answer['status']=='UNREACHABLE'
 elif r['failure']['status']=='UNREACHABLE':assert repairs==4 and answer['status']=='UNREACHABLE'
 else:raise AssertionError('unsupported terminal verifier case')
assert all(c<=audit.caps[n] for n,c in ledger.items())
p=json.loads((out/'protocol.json').read_text())
for name,h in p['sources'].items():assert sha(root/'tools'/name)==h
(out/'verification.json').write_text(json.dumps({'retained_connections':len(records),'successful_witnesses_checked':witnesses,'releases':releases,'repairs':repairs,'overflow_units':0,'multi_parent_nodes':0,'receipt_sha256':sha(out/'receipt.json'),'scope':'OriginalXML inheritedhistory/exact1ns/cost/wholeNET release/queue/cut/ledger/parents audited. No nativeFULL/STA or netbenefit; incomplete states not published.'},indent=2)+'\n');print('verified',len(records),'paths;',repairs,'repairs')
