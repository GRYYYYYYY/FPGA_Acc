"""One frozen certified-frontier wholeNET release/reroute experiment."""
import json,time
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_capacity_rc_search import NativeCapacityRC
root=Path(__file__).resolve().parents[1];parent=root/'experiments/nonzero_rc_ex5p_joint_delay_2026-10-06';r=json.loads((parent/'receipt.json').read_text());proof=json.loads((parent/'verification.json').read_text());assert proof['receipt_sha256']==sha(parent/'receipt.json') and proof['frozen_residual_disconnection_certified'];out=root/'experiments/ex5p_frontier_repair_2026-10-06';out.mkdir();ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json';(out/'protocol.json').write_text(json.dumps({'parent_sha256':sha(parent/'receipt.json'),'proof_sha256':sha(parent/'verification.json'),'repairs':1,'budget_ns':1,'max_labels':10000,'policy':'Release all wholeNET owners of certified full frontier except failedNET; retry failed query, releasedNET allqueries NET/connection order, then untouched pending; exact delay costs/hardcapacity; stop any query failure or multiparent, no added fallback'},indent=2)+'\n');start=time.monotonic();graph,digest,nodes,f,rc,queries=load_endpoints(ep);native=NativeCapacityRC(rc)
for slot in range(len(rc.increments)):native.arrays[3][slot]=rc.increments[slot]
slots={f['edge_ids'][s]:(u,f['dest_ranks'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};unions=defaultdict(set);parents=defaultdict(dict);records={q['connection_id']:q for q in r['records']}
for record in r['records']:
 net=record['net_id'];unions[net].add(record['source'])
 for eid in record['answer']['physical_edge_ids']:u,v=slots[eid];unions[net].add(v);parents[net][v]=(u,eid)
ledger=Counter(n for used in unions.values() for n in used);assert dict(ledger)=={int(n):c for n,c in r['ledger'].items()};failed=r['failure']['query'];frontier=proof['blocked_frontier_nodes'];owners={n:sorted(net for net,used in unions.items() if n in used and net!=failed['net_id']) for n in frontier};blockers=sorted({net for nets in owners.values() for net in nets});removed=[q for q in r['records'] if q['net_id'] in blockers];released={net:sorted(unions[net]) for net in blockers}
for net in blockers:
 ledger.subtract(unions[net]);del unions[net];del parents[net]
ledger=+ledger
for q in removed:del records[q['connection_id']]
queue=[failed]+[q for q in sorted(queries,key=lambda q:(q['net_id'],q['connection_id'])) if q['net_id'] in blockers]+[q for q in queries if q['connection_id']>=failed['connection_id'] and q['connection_id']!=failed['connection_id'] and q['net_id'] not in blockers];attempts=[];failure=None
for q in queue:
 net=q['net_id'];other=dict(ledger)
 for n in unions[net]:other[n]-=1
 other={n:c for n,c in other.items() if c};native.set_other(other);answer=native.query(q['source'],q['sink'],rc.scale//10**9,max_labels=10000);attempts.append({'query':q,'answer':answer})
 if answer['status']!='FOUND':failure={'query':q,'status':answer['status']};break
 used={q['source']};node=q['source'];incoming={}
 for eid in answer['physical_edge_ids']:u,v=slots[eid];assert node==u;node=v;used.add(v);incoming[v]=(u,eid)
 assert node==q['sink'];conflicts=[n for n,p in incoming.items() if n in parents[net] and parents[net][n]!=p]
 if conflicts:failure={'query':q,'status':'MULTI_PARENT_REJECTED','nodes':conflicts};break
 assert q['connection_id'] not in records;parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);records[q['connection_id']]={**q,'mode':'NATIVE_DELAY_COST','answer':answer}
result={'status':'COMPLETE_DIAGNOSTIC' if failure is None else 'INCOMPLETE_NOT_PUBLISHABLE','records':[records[k] for k in sorted(records)],'completed_connections':len(records),'required_connections':len(queries),'attempts':attempts,'failure':failure,'release':{'frontier_owners':owners,'blocker_NETs':blockers,'removed_connection_ids':[q['connection_id'] for q in removed],'released_unions':released},'ledger':dict(ledger),'graph_sha256':digest,'scale':rc.scale,'total_context_repair_seconds':time.monotonic()-start,'parent_sha256':sha(parent/'receipt.json'),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],'retained',len(records),'blockers',blockers,'removed',len(removed),'attempts',len(attempts),'failure',failure)
