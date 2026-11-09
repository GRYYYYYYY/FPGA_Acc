"""Frozen complete-NET tree pool packing from archived negotiated proposals."""
import sys,json,time,copy
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
parent=R/'experiments/misex_net466_extra_owner_joint_v17_2026-10-07';out=R/'experiments/misex_net466_tree_pool_v1_2026-10-07';out.mkdir();rp=parent/'receipt.json';receipt=json.loads(rp.read_text());bindings={**receipt['bindings'],**receipt['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==v for k,v in bindings.items());(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,max_candidates=8,max_search_nodes=100000,deadline_seconds=120,pool='For each same release scope, complete original trees plus all successful independent whole-NET proposals from archived rounds; deduplicate by complete physical paths. Preserve fixed kept and every selected/released CID.',order='Static fewest options then NET ID; original option first then numeric round order; exact node-union capacity pruning.',scope='Finite frozen candidate tree combinations, not new path generation/global solver/native or workflow gain.'),indent=2)+'\n');begin=time.perf_counter();event=json.loads((parent/'event.json').read_text());(out/'event.json').write_text(json.dumps(event)+'\n');_,_,nodes,f,rc,queries=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={e:i for i,e in enumerate(f['edge_ids'])}
def occupied(records):
 own=set()
 for rec in records:own.add(rec['source']);own.update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
 return own
attempts=[];solution=None;deadline=time.perf_counter()+120
for a in receipt['attempts']:
 release=set(a['release']);kept=[r for r in event['before_records'] if r['net_id'] not in release];groups=defaultdict(set)
 for rec in event['before_records']:
  if rec['net_id'] in release:groups[rec['net_id']].add(rec['connection_id'])
 for q in event['selection']['queries']:groups[q['net_id']].add(q['connection_id'])
 pool={n:[] for n in groups};seen={n:set() for n in groups}
 def add(net,records,origin):
  records=sorted(records,key=lambda r:r['connection_id'])
  if {r['connection_id'] for r in records}!=groups[net]:return
  key=tuple((r['connection_id'],tuple(r['answer']['physical_edge_ids'])) for r in records)
  if key not in seen[net]:seen[net].add(key);pool[net].append(dict(records=records,origin=origin,nodes=occupied(records)))
 for net in groups:add(net,[r for r in event['before_records'] if r['net_id']==net],'original')
 for b in a['branches']:
  d=parent/f"attempt{a['index']}_branch{b['index']}"
  for net in groups:
   p=d/f'net{net}.json'
   if p.exists():
    state=json.loads(p.read_text())
    if state['failure'] is None:add(net,[r for r in state['records'] if r['net_id']==net],str(p))
 nets=sorted(groups,key=lambda net:(len(pool[net]),net));owners=defaultdict(set)
 for rec in kept:owners[rec['net_id']].update(occupied([rec]))
 ledger=Counter(n for own in owners.values() for n in own);assert all(v<=f['capacities'][n] for n,v in ledger.items());chosen={};visits=0;limited=False
 def dfs(index):
  global visits,limited
  if visits>=100000 or time.perf_counter()>=deadline:limited=True;return False
  visits+=1
  if index==len(nets):return True
  net=nets[index]
  for option in pool[net]:
   if any(ledger[n]>=f['capacities'][n] for n in option['nodes']):continue
   ledger.update(option['nodes']);chosen[net]=option
   if dfs(index+1):return True
   ledger.subtract(option['nodes']);del chosen[net]
   if limited:return False
  return False
 found=dfs(0);status='FOUND_POOL_BATCH' if found else 'DEADLINE' if time.perf_counter()>=deadline else 'SEARCH_NODE_LIMIT' if limited else 'POOL_EXHAUSTED';attempts.append(dict(index=a['index'],release=a['release'],variant_counts={str(n):len(pool[n]) for n in nets},net_order=nets,search_nodes=visits,status=status));print(attempts[-1],flush=True)
 if found:
  records=kept+[r for n in nets for r in chosen[n]['records']];expected={r['connection_id'] for r in event['before_records']}|set(event['selection']['requested_connection_ids']);assert {r['connection_id'] for r in records}==expected
  solution=dict(records=sorted(records,key=lambda r:r['connection_id']),ledger={n:c for n,c in ledger.items() if c},completed_connections=len(records),required_connections=len(queries),failure=None,pending_connection_ids=sorted({q['connection_id'] for q in queries}-expected),selected_origins={str(n):chosen[n]['origin'] for n in nets},released_net_ids=a['release']);break
 if time.perf_counter()>=deadline:break
(out/'candidate.json').write_text(json.dumps(solution)+'\n');assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,attempts=attempts,completed=None if solution is None else len(solution['records']),required=len(queries),total_component_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
