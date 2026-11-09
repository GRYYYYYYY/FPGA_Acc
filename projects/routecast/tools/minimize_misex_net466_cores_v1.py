"""Post-outcome bounded deletion minimization of ordinary overbudget cores."""
import json,sys,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from pending_owner_joint_repair_v3 import constrained_witness
parent=R/'experiments/misex_net466_extra_owner_joint_v9_2026-10-07';rp=parent/'receipt.json';r=json.loads(rp.read_text());event=json.loads((parent/'event.json').read_text());out=R/'experiments/misex_net466_minimal_cores_v1_2026-10-07';out.mkdir();bindings={**r['bindings'],str(rp):sha(rp),str(parent/'event.json'):sha(parent/'event.json'),**closure([Path(__file__)])};assert all(sha(k)==v for k,v in bindings.items());_,_,nodes,f,rc,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={e:i for i,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in event['before_records']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
start=time.perf_counter();deadline=start+120;rows=[];checks=0
for a in r['attempts']:
 for b in a['branches']:
  for c in b.get('ordinary_cores',[]):
   net=c['net'];occupancy=Counter(n for owner,own in owners.items() if owner not in a['release'] and owner!=net for n in own);blocked={n for n,count in occupancy.items() if count>=f['capacities'][n]};bans=set(c['bans']);tests=[]
   for node in sorted(bans):
    if checks>=256 or time.perf_counter()>=deadline:break
    trial=bans-{node}
    try:w=constrained_witness(f,rc,c['query'],trial|blocked,deadline)
    except TimeoutError:break
    checks+=1;infeasible=w is None or w['minimum_integer']>c['budget'];tests.append(dict(removed_node=node,bans=sorted(trial),minimum_integer=None if w is None else w['minimum_integer'],physical_edge_ids=None if w is None else w['physical_edge_ids'],ordinary_infeasible=infeasible))
    if infeasible:bans=trial
   rows.append(dict(attempt=a['index'],branch=b['index'],release=a['release'],query=c['query'],budget=c['budget'],original_bans=c['bans'],reduced_bans=sorted(bans),tests=tests));print(a['index'],b['index'],net,len(c['bans']),len(bans),flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,checks=checks,elapsed_seconds=time.perf_counter()-start,scope='Paid saved-branch deletion heuristic; each retained reduction requires exact ordinary certificate. Not global infeasibility, native QoR or from-empty gain.'),indent=2)+'\n')
