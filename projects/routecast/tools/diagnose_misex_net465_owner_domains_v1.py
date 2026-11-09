"""Paid post-outcome failure domains, bounded single-extra checks; no joint claim."""
import sys,json,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from budget_owner_screen_v2 import screen,witness_in_domain
parent=R/'experiments/misex_net465_failure_minima_v1_2026-10-07';rp=parent/'receipt.json';vp=parent/'verification.json';r=json.loads(rp.read_text());v=json.loads(vp.read_text());assert v['rows_verified']==len(r['rows']) and v['ordinary_feasible_failures']==0;out=R/'experiments/misex_net465_failure_owner_domains_v1_2026-10-07';out.mkdir();bindings={**r['bindings'],**v['bindings'],**closure([Path(__file__)]),str(rp):sha(rp),str(vp):sha(vp)};assert all(sha(k)==h for k,h in bindings.items());(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,max_checks_per_domain=128,deadline_seconds=120,scope='Post-outcome saved failure single-extra-owner conditioned ordinary witnesses; no joint feasibility, domain completeness outside this condition, equal-work ablation, native benefit or general infeasibility claim.'))+'\n');_,_,nodes,f,rc,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');event=json.loads((R/'experiments/misex_window_witness_guided_joint_v32_2026-10-07/event.json').read_text());slots={e:s for s,e in enumerate(f['edge_ids'])};allowners=defaultdict(set)
for rec in event['before_records']:allowners[rec['net_id']].add(rec['source']);allowners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
start=time.perf_counter();deadline=start+120;rows=[];memo={}
for failed in r['rows']:
 q=failed['query'];key=(tuple(failed['release']),q['connection_id'],tuple(failed['bans']));owners={net:ns for net,ns in allowners.items() if net not in failed['release']}
 if key not in memo:
  domain=screen(f,rc,q,frozenset(failed['bans']),owners,failed['budget'],deadline);other=Counter(n for net,ns in owners.items() if net!=q['net_id'] for n in ns);assert witness_in_domain(f,rc,q,domain,other,set(),failed['budget'],deadline) is None;checks=[]
  for net in domain['candidates'][:128]:checks.append(dict(extra_net=net,witness=witness_in_domain(f,rc,q,domain,other,owners[net],failed['budget'],deadline)))
  memo[key]=dict(domain=domain,checks=checks)
 row=dict(branch_file=failed['branch_file'],query=q,release=failed['release'],bans=failed['bans'],budget=failed['budget'],**memo[key]);rows.append(row);print(Path(failed['branch_file']).parent.name,q['net_id'],'domain',len(row['domain']['candidates']),'restoring',[x['extra_net'] for x in row['checks'] if x['witness'] is not None],flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),elapsed_seconds=time.perf_counter()-start,rows=rows,bindings=bindings),indent=2)+'\n')
