"""Bounded whole-window necessary conditions for single/pair releases, no NET hardcoding."""
import sys,json,time,itertools
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from budget_owner_screen_v2 import screen
from fresh_release_root_screen_v2 import FreshRootScreen
from pending_owner_joint_repair_v3 import constrained_witness
parent=R/'experiments/misex_verified_seed_continuation_v14_2026-10-07';rp=parent/'receipt.json';r=json.loads(rp.read_text());vp=parent/'verification.json';proof=json.loads(vp.read_text());bindings={**proof['bindings'],**closure([Path(__file__)]),str(rp):sha(rp),str(vp):sha(vp)};assert all(sha(k)==h for k,h in bindings.items());out=R/'experiments/misex_net_window_witness_guided_v11_2026-10-07';out.mkdir();_,_,nodes,f,rc,queries=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');state=json.loads((parent/'candidate.json').read_text());before=state['records'];done={rec['connection_id'] for rec in before};net=state['failure']['query']['net_id'];selected=sorted([q for q in queries if q['net_id']==net and q['connection_id'] not in done],key=lambda q:q['connection_id'])[:16];assert selected and selected[0]==state['failure']['query'];event=dict(before_records=before,selection=dict(queries=selected,requested_connection_ids=[q['connection_id'] for q in selected]));eventfile=out/'event.json';eventfile.write_text(json.dumps(event)+'\n');bindings[str(eventfile)]=sha(eventfile);(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,max_checks=128,max_candidates=4,max_extra_owners=6,deadline_seconds=120,scope='Post-outcome all-selected fresh root necessary conditions; original cheapest-path saturated-owner sets and their unions prioritized before bounded pair coverage; heuristic, not joint completeness or full gain.'))+'\n');event=json.loads(eventfile.read_text());floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json').read_text())};start=time.perf_counter();deadline=start+120;context=FreshRootScreen(f,rc,event['before_records'],floors);counts=Counter(rec['net_id'] for rec in event['before_records']);domains=[];extras=set()
for q in event['selection']['queries']:
 budget=max(rc.scale//10**9,(3*floors[(q['source'],q['sink'])]+1)//2);domain=screen(f,rc,q,frozenset(),context.owners,budget,deadline);domains.append(dict(query=q,budget=budget,domain=domain));extras.update(domain['candidates'])
base={q['net_id'] for q in event['selection']['queries']} & context.owners.keys();candidates={frozenset(base)|frozenset(extra) for size in (1,2) for extra in itertools.combinations(sorted(extras-base),size)};witness_sets=[];witness_evidence=[];slots={e:s for s,e in enumerate(f['edge_ids'])}
for q in event['selection']['queries']:
 witness=constrained_witness(f,rc,q,frozenset(),deadline);budget=max(rc.scale//10**9,(3*floors[(q['source'],q['sink'])]+1)//2)
 if witness is None or witness['minimum_integer']>budget:continue
 used={q['source']}|{f['dest_ranks'][slots[e]] for e in witness['physical_edge_ids']};occupancy=Counter(n for net,ns in context.owners.items() if net!=q['net_id'] for n in ns);blocked={n for n in used if occupancy[n]>=f['capacities'][n]};blockers=frozenset(net for net,ns in context.owners.items() if net!=q['net_id'] and ns.intersection(blocked));witness_evidence.append(dict(query=q,witness=witness,blocked_nodes=sorted(blocked),blocking_net_ids=sorted(blockers)))
 if blockers:witness_sets.append(blockers|base)
guided=set(witness_sets)
for left,right in itertools.combinations(witness_sets,2):guided.add(left|right)
if witness_sets:guided.add(frozenset().union(*witness_sets))
rank=lambda ns:(sum(counts[n] for n in ns),len(ns),tuple(sorted(ns)))
guided={ns for ns in guided if 0<len(ns)<=6};ordered=sorted(guided,key=rank)+sorted(candidates-guided,key=rank);checks=[];accepted=[]
for release in ordered[:128]:
 root=context.check(release,event['selection']['queries'],deadline);checks.append(root)
 if root['all_selected_ordinary_budget_feasible']:accepted.append(sorted(release))
 if len(accepted)==4:break
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,domains=domains,witness_evidence=witness_evidence,guided_release_sets=[sorted(ns) for ns in sorted(guided,key=rank)],checks=checks,proposed=accepted,event_file=str(eventfile),elapsed_seconds=time.perf_counter()-start),indent=2)+'\n');print('ROOT PAIRS',len(checks),accepted,flush=True)
