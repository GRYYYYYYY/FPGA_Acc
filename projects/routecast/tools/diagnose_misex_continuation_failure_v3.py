"""Single new capacity failure diagnosis and bounded whole-owner restoring witnesses."""
import sys,json,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from budget_owner_screen_v2 import screen,witness_in_domain
from pending_owner_joint_repair_v3 import constrained_witness
parent=R/'experiments/misex_verified_seed_continuation_v3_2026-10-07';out=R/'experiments/misex_continuation_failure_domain_v3_2026-10-07';out.mkdir();vp=parent/'verification.json';proof=json.loads(vp.read_text());bindings={**proof['bindings'],**closure([Path(__file__)]),str(vp):sha(vp)};assert all(sha(k)==h for k,h in bindings.items());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';_,_,nodes,f,rc,queries=load_endpoints(ep);state=json.loads((parent/'candidate.json').read_text());failure=state['failure'];q=failure['query'];budget=failure['budget_integer'];slots={e:s for s,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in state['records']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy='Failure query, no branch bans, fixed before capacities excluding own NET, full raw budget domain, at most128 single-extra checks,120s.',scope='Post-outcome scalar-RC diagnosis; single-extra witnesses are not whole-NET joint solutions.'))+'\n');start=time.perf_counter();deadline=start+120;other=Counter(n for net,ns in owners.items() if net!=q['net_id'] for n in ns);forbidden=frozenset(n for n in range(len(nodes)) if other[n]>=f['capacities'][n]);baseline=constrained_witness(f,rc,q,forbidden,deadline);domain=screen(f,rc,q,frozenset(),owners,budget,deadline);checks=[]
for net in domain['candidates'][:128]:checks.append(dict(extra_net=net,witness=witness_in_domain(f,rc,q,domain,other,owners[net],budget,deadline)))
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,query=q,budget=budget,baseline=baseline,domain=domain,checks=checks,elapsed_seconds=time.perf_counter()-start),indent=2)+'\n');print('DIAGNOSIS',q,'baseline',baseline,'candidates',len(domain['candidates']),'restoring',[x['extra_net'] for x in checks if x['witness'] is not None],flush=True)
