"""Independent archived whole-NET capacity ledger and overload split choice."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_extra_owner_joint_v4_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)}
assert all(sha(k)==h for k,h in bindings.items())
_,_,nodes,f,rc,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={e:i for i,e in enumerate(f['edge_ids'])};rows=[]
for directory in sorted(out.glob('attempt*_branch*')):
 b=json.loads((directory/'branch.json').read_text())['branch']
 if b['status']!='SPLIT':continue
 assert all(v is None for v in b['failures'].values());owners=defaultdict(set);nets=set()
 for path in directory.glob('net*.json'):
  net=int(path.stem[3:]);nets.add(net);state=json.loads(path.read_text());assert state['failure'] is None
  for rec in state['records']:
   owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
 ledger=Counter(n for own in owners.values() for n in own);conflicts=[n for n,c in ledger.items() if c>f['capacities'][n]];assert len(conflicts)==b['conflict_count']
 ranked=sorted((-(ledger[n]-f['capacities'][n]),-len([net for net in nets if n in owners[net]]),n) for n in conflicts);expected=ranked[0][2];participants=sorted(net for net in nets if expected in owners[net]);assert expected==b['conflict_node'] and ledger[expected]-f['capacities'][expected]==b['conflict_excess'] and participants==b['conflict_participants']
 assert all((net,expected) not in {tuple(x) for x in b['constraints']} for net in participants)
 rows.append(dict(branch=directory.name,node=expected,participants=participants,excess=b['conflict_excess'],differs_from_smallest_node=expected!=min(conflicts)))
assert all(sha(k)==h for k,h in bindings.items());(out/'conflict_priority_verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Archived split ledgers and priority only; no completeness or gain claim.'),indent=2)+'\n');print('PASS conflict priority',len(rows),sum(x['differs_from_smallest_node'] for x in rows))
