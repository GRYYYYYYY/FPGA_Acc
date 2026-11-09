"""Independent every-stage ledger rebuild plus failed-operation atomicity checks."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from transaction_shared_tree_ledger_v1 import TransactionLedger
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'transaction_shared_tree_ledger_v1_2026-10-08';D.mkdir(exist_ok=False)
case=next(c for c in json.loads((E/'owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
queries={q['connection_id']:q for q in json.loads(Path(case['target']).read_text())['connections']}
from class_cached_rc_endpoint_context_v1 import load_endpoints
graph,digest,nodes,fields,rc,_=load_endpoints(Path(case['target']))
bp=E/'fresh_native_budget_repairs_v1_2026-10-08/receipt.json';base=json.loads(bp.read_text())['state'];base={int(cid):tuple(tuple(x) for x in path) for cid,path in base.items()}
rp=E/'fresh_critical_owner_transactions_v1_2026-10-08/receipt.json';rows=json.loads(rp.read_text())['rows']
checks=0
def check(ledger):
 global checks
 counts=defaultdict(Counter);parents=defaultdict(dict);uses=defaultdict(Counter)
 for cid,path in ledger.state.items():
  net=ledger.queries[cid]['net_id']
  counts[net].update(n for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):
   assert v not in parents[net] or parents[net][v]==(u,s)
   parents[net][v]=(u,s);uses[net][v]+=1
 normalize=lambda obj:{k:dict(v) for k,v in obj.items() if v}
 assert normalize(ledger.nodes)==normalize(counts)
 assert normalize(ledger.parents)==normalize(parents)
 assert normalize(ledger.parent_uses)==normalize(uses)
 occupancy=Counter(n for used in counts.values() for n in used)
 assert ledger.occupancy==occupancy and all(v<=ledger.capacities[n] for n,v in occupancy.items())
 representatives={q['net_id']:cid for cid,q in ledger.queries.items()}
 for net,cid in representatives.items():
  for node in counts[net]:assert ledger.outside(cid,node)==occupancy[node]-1
  foreign=next((node for node in occupancy if node not in counts[net]),None)
  if foreign is not None:assert ledger.outside(cid,foreign)==occupancy[foreign]
 checks+=1
for row in rows:
 t=TransactionLedger(base,queries,fields['capacities'],{})
 for cid in set(row['plan']['released_connections'])|{row['plan']['critical']}:t.release(cid);check(t)
 for event in row['events']:
  check(t);assert event['status']=='STAGED'
  t.insert(event['connection_id'],event['path']);check(t)
 assert {str(cid):[list(x) for x in path] for cid,path in t.state.items()}==row['state']
q={0:dict(source=0,sink=3,net_id=0),1:dict(source=0,sink=4,net_id=0),2:dict(source=5,sink=6,net_id=1)}
initial={0:((0,None),(1,0),(3,0)),1:((0,None),(1,0),(4,0)),2:((5,None),(2,0),(6,0))}
t=TransactionLedger(initial,q,[1]*8,{n:1 for n in range(8)});t.release(0);check(t)
def snapshot(t):return repr((t.state,dict(t.nodes),dict(t.parents),dict(t.parent_uses),t.occupancy,t.wire))
failures=0
for operation in (lambda:t.insert(0,[(1,None),(3,0)]),lambda:t.insert(0,[(0,None),(2,0),(3,0)]),lambda:t.insert(0,[(0,None),(7,0),(1,0),(3,0)]),lambda:t.insert(1,initial[1]),lambda:t.release(999)):
 before=snapshot(t)
 try:operation()
 except (AssertionError,KeyError):failures+=1
 else:raise AssertionError('invalid operation accepted')
 assert snapshot(t)==before;check(t)
t.insert(0,initial[0]);check(t);t.release(0);t.release(1);check(t);t.insert(0,[(0,None),(7,0),(3,0)]);t.insert(1,initial[1]);check(t)
assert initial[0]==((0,None),(1,0),(3,0)) and failures==5
paths=[bp,rp,Path(case['target']),graph,Path(__file__),R/'tools/transaction_shared_tree_ledger_v1.py',R/'tools/incremental_shared_tree_ledger_v1.py']
bindings={str(p):sha(p) for p in paths};assert bindings[str(graph)]==digest
out=dict(bindings=bindings,all_four_transaction_trace_reference_counts_parents_capacity_pass=True,complete_state_rebuild_checks=checks,
 failed_operation_atomicity_cases=failures,scope='Every release and before/after insert of all102 accepted historical transaction stages independently rebuilt; complete final states equal. Synthetic shared-prefix reference removal/restoration and five rejection atomicity cases covered. Physical arcs/RC/budget/native remain separately certified.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'},flush=True)
