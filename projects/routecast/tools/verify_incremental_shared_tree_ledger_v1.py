"""Compare incremental state to fresh full-state reconstruction at every query."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from incremental_shared_tree_ledger_v1 import SharedTreeLedger
R=Path(__file__).resolve().parents[1];D=R/'experiments/incremental_shared_tree_ledger_v1_2026-10-08';D.mkdir(exist_ok=False)
names=('complete_wire_contraction_v1_2026-10-08','complete_wire_contraction_v2_2026-10-08','global_guard_wire_contraction_v1_2026-10-08');proofnames=('verification.json','verification_v3.json','verification.json')
bindings={str(Path(__file__)):sha(Path(__file__)),str(R/'tools/incremental_shared_tree_ledger_v1.py'):sha(R/'tools/incremental_shared_tree_ledger_v1.py'),str(R/'tools/class_cached_rc_endpoint_context_v1.py'):sha(R/'tools/class_cached_rc_endpoint_context_v1.py')};receipts=[]
for name,pn in zip(names,proofnames):
 directory=R/'experiments'/name;p=json.loads((directory/pn).read_text());assert all(sha(f)==h for f,h in p['bindings'].items());bindings.update(p['bindings'])
 for path in (directory/pn,directory/'receipt.json'):bindings[str(path)]=sha(path)
 receipts.append(json.loads((directory/'receipt.json').read_text()))
bp=R/'experiments/critical_owner_transaction_v1_2026-10-08/receipt.json';bindings[str(bp)]=sha(bp);state={int(cid):tuple(tuple(x) for x in path) for cid,path in json.loads(bp.read_text())['rows'][0]['state'].items()}
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
graph,digest,nodes,f,rc,queries=load_endpoints(Path(case['target']));byid={q['connection_id']:q for q in queries};length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
ledger=SharedTreeLedger(state,byid,f['capacities'],length);events=commits=0
for name,receipt in zip(names,receipts):
 assert len(receipt['events'])==1929
 for event in receipt['events']:
  cid=event['connection_id'];net=byid[cid]['net_id'];unions=defaultdict(set);uses=defaultdict(Counter);parents=defaultdict(dict);parentuses=defaultdict(Counter);kept=set();fixed={}
  for other,path in state.items():
   owner=byid[other]['net_id'];unions[owner].update(n for n,s in path);uses[owner].update(n for n,s in path)
   for (u,_),(v,s) in zip(path,path[1:]):assert v not in parents[owner] or parents[owner][v]==(u,s);parents[owner][v]=(u,s);parentuses[owner][v]+=1
   if other!=cid and owner==net:
    kept.update(n for n,s in path)
    for (u,_),(v,s) in zip(path,path[1:]):assert v not in fixed or fixed[v]==(u,s);fixed[v]=(u,s)
  full=Counter(n for ns in unions.values() for n in ns)
  assert ledger.state==state and ledger.nodes==uses and ledger.parents==parents and ledger.parent_uses==parentuses and ledger.occupancy==full
  wire={owner:sum(length.get(n,0) for n in ns) for owner,ns in unions.items()};assert ledger.wire==Counter(wire)
  assert ledger.view(cid)==(kept,fixed)
  # These supports cover every nonzero outside count; all absent nodes are zero.
  assert all(ledger.outside(cid,n)==full[n]-int(n in unions[net]) for n in full)
  before={k:v for k,v in state.items()}
  if event['status']=='COMMIT':
   path=tuple(tuple(x) for x in event['new_path']);ledger.replace(cid,path);state[cid]=path;commits+=1
   assert all(ledger.state[k]==v for k,v in before.items() if k!=cid)
  events+=1
  if events%250==0:print('verified',events,'/5787 ledger queries',flush=True)
 assert receipt['state']=={str(cid):[list(x) for x in path] for cid,path in state.items()}
# Verify the last committed state even if the last query itself was a commit.
final=SharedTreeLedger(state,byid,f['capacities'],length)
assert ledger.nodes==final.nodes and ledger.parents==final.parents and ledger.parent_uses==final.parent_uses and ledger.occupancy==final.occupancy and ledger.wire==final.wire
assert events==5787 and commits==169 and sum(ledger.wire.values())==11474 and all(sha(f)==h for f,h in bindings.items())
report=dict(bindings=bindings,all5787_query_constraints_equal_fresh_full_state=True,commits=commits,final_wire=11474,scope='Complete development traces: perNET branch uses, parent uses, uniqueNET occupancy, outside counts, kept sets, fixed parents and wire are identical to fresh full-state construction at every query. No physical/RC/STA contract expansion or runtime gain claim; search integration still required.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS complete5787 ledger states and169 commits',flush=True)
