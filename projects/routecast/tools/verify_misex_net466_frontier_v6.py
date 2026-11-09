"""Independent replay of heuristic frontier priority and visited branch order."""
import json,heapq,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=R/'experiments/misex_net466_extra_owner_joint_v6_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],str(rp):sha(rp),str(Path(__file__).resolve()):sha(__file__)};assert all(sha(k)==v for k,v in bindings.items());rows=[]
for attempt in r['attempts']:
 queue=[(0,0,0,frozenset())];seen={frozenset()};serial=0
 for i,b in enumerate(attempt['branches']):
  score,depth,order,expected=heapq.heappop(queue);assert b['index']==i and frozenset(tuple(x) for x in b['constraints'])==expected
  if b['status']=='SPLIT':
   participants=b['conflict_participants'];assert participants==sorted(participants) and len(participants)>=2
   for net in reversed(participants):
    child=expected|{(net,b['conflict_node'])}
    if child not in seen:
     seen.add(child);serial+=1;heapq.heappush(queue,(b['conflict_count'],len(child),serial,child))
  rows.append(dict(attempt=attempt['index'],branch=i,parent_conflicts=score,depth=depth,insertion_order=order))
assert all(sha(k)==v for k,v in bindings.items());(out/'frontier_verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Priority queue and exact recorded prefix only; no feasibility or global completeness proof.'),indent=2)+'\n');print('PASS frontier',len(rows))
