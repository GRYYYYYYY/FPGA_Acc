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
parent=R/'experiments/misex_continuation_net_window_joint_v3_2026-10-07';rp=parent/'receipt.json';r=json.loads(rp.read_text());eventfile=parent/'event.json';assert sha(eventfile)==r['files'][str(eventfile)];bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp),str(eventfile):sha(eventfile)};assert all(sha(k)==h for k,h in bindings.items());out=R/'experiments/misex_net_window_root_pairs_v1_2026-10-07';out.mkdir();(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,max_checks=128,max_candidates=4,max_extra_owners=2,deadline_seconds=120,scope='Post-outcome all-selected fresh root necessary conditions; domain union and bounded pair coverage heuristic, not joint completeness or full gain.'))+'\n');_,_,nodes,f,rc,queries=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');event=json.loads(eventfile.read_text());floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json').read_text())};start=time.perf_counter();deadline=start+120;context=FreshRootScreen(f,rc,event['before_records'],floors);counts=Counter(rec['net_id'] for rec in event['before_records']);domains=[];extras=set()
for q in event['selection']['queries']:
 budget=max(rc.scale//10**9,(3*floors[(q['source'],q['sink'])]+1)//2);domain=screen(f,rc,q,frozenset(),context.owners,budget,deadline);domains.append(dict(query=q,budget=budget,domain=domain));extras.update(domain['candidates'])
base={q['net_id'] for q in event['selection']['queries']} & context.owners.keys();candidates={frozenset(base)|frozenset(extra) for size in (1,2) for extra in itertools.combinations(sorted(extras-base),size)};ordered=sorted(candidates,key=lambda ns:(sum(counts[n] for n in ns),len(ns),tuple(sorted(ns))));checks=[];accepted=[]
for release in ordered[:128]:
 root=context.check(release,event['selection']['queries'],deadline);checks.append(root)
 if root['all_selected_ordinary_budget_feasible']:accepted.append(sorted(release))
 if len(accepted)==4:break
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,domains=domains,checks=checks,proposed=accepted,event_file=str(eventfile),elapsed_seconds=time.perf_counter()-start),indent=2)+'\n');print('ROOT PAIRS',len(checks),accepted,flush=True)
