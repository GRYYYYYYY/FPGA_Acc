"""Independent XML path, history, queue, cut and wholeNET mutation event replay."""
import json
from pathlib import Path
from collections import Counter,defaultdict,deque
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_explicit_budget_engine_v2_2026-10-06';r=json.loads((out/'receipt.json').read_text());parent=root/'experiments/ex5p_bounded_history_repair_2026-10-06';prior=json.loads((parent/'receipt.json').read_text());verified=json.loads((parent/'verification.json').read_text());assert verified['receipt_sha256']==sha(parent/'receipt.json') and r['parent_sha256']==sha(parent/'receipt.json') and r['protocol_sha256']==sha(out/'protocol.json') and r['source_sha256']==sha(root/'tools/trial_ex5p_explicit_budget_engine.py');ep=json.loads((root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json').read_text());assert all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values());audit=ImmutableXMLAudit(Path(ep['inputs']['graph']['path']),r['graph_sha256']);ids,classes,switches,_=read(Path(ep['inputs']['graph']['path']));adj=defaultdict(list)
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
  assert event['type']=='RELEASE' and last is not None and repairs<4;q,other,answer=last;assert answer['status']=='UNREACHABLE' and event['failed_query']==q;node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2
  for eid in event['empty_path']:
   e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],e.switch_id)
  assert node==q['sink'] and delay*r['scale']==event['empty_delay_integer'] and delay<=Fraction(1,10**9)
  frontier=sorted(n for n in used if other.get(n,0)>=audit.caps[n]);assert frontier==event['frontier'];owners={n:sorted(k for k,ns in unions.items() if k!=q['net_id'] and n in ns) for n in frontier};blockers=sorted({k for ks in owners.values() for k in ks}|({q['net_id']} if unions[q['net_id']] else set()));assert owners=={int(n):ks for n,ks in event['owners'].items()} and blockers==event['blocker_NETs'];removed=sorted(cid for cid,row in records.items() if row['net_id'] in blockers);assert removed==event['removed_connection_ids'];assert {k:sorted(unions[k]) for k in blockers}=={int(k):ns for k,ns in event['released_unions'].items()}
  for k in blockers:ledger.subtract(unions[k]);del unions[k];del parents[k]
  ledger=+ledger
  for cid in removed:del records[cid]
  history.update(frontier);assert dict(history)=={int(n):c for n,c in event['history_after'].items()};pending=deque([q]+[x for x in queries if x['net_id']==q['net_id'] and x['connection_id']!=q['connection_id'] and q['net_id'] in blockers]+[x for x in sorted(queries,key=lambda x:(x['net_id'],x['connection_id'])) if x['net_id'] in blockers and x['net_id']!=q['net_id']]+[x for x in pending if x['net_id'] not in blockers]);repairs+=1;releases.append({'NETs':blockers,'removed':len(removed),'frontier':len(frontier)})
assert repairs==r['repairs']==1 and [records[k] for k in sorted(records)]==r['records'] and dict(ledger)=={int(n):c for n,c in r['ledger'].items()} and dict(history)=={int(n):c for n,c in r['history'].items()};assert not pending and r['failure'] is None and len(records)==r['completed_connections']==r['required_connections']==1916 and r['status']=='COMPLETE_DIAGNOSTIC';assert all(c<=audit.caps[n] for n,c in ledger.items());(out/'verification.json').write_text(json.dumps({'complete_connections':1916,'successful_witnesses_checked':witnesses,'releases':releases,'repairs':1,'overflow_units':0,'multi_parent_nodes':0,'receipt_sha256':sha(out/'receipt.json'),'scope':'Independent originalXML1ns/history-cost/wholeNET release/queue/ledger/parents replay validates COMPLETE1916 physical candidate. Release path feasibility checked, empty-path minimum optimality not separately certified here. Nativepin identity/FULL/STA and end-to-end benefit not yet proven.'},indent=2)+'\n');print('verified COMPLETE1916 paths;1 budget repair, zerooverflow/parents')
