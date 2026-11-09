"""Conflict-proof guided new paths and finite bank joint selection, no target paths."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_bounded_wire_search_v1 import NativeBoundedSearch
from finite_route_bank_solver_v1 import solve
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'online_cost_replay_v1_adder_online_owner337_detours_v1_2026-10-09';D=E/'online_cost_replay_v1_adder_online_support_closure_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();vp=E/'online_cost_replay_v1_adder_online_component_verification_v3_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';g,h,nodes,f,rc,_=load_endpoints(ep0);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
edge={f['edge_ids'][i]:(u,f['dest_ranks'][i],f['switch_ids'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};search=NativeBoundedSearch(rc,length);bindings.update(search.bindings);cap=f['capacities'];rows=[]
from finite_route_bank_arc_consistency_v1 import propagate
step=3;ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';bp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_3_budgets.json';q={x['connection_id']:x for x in json.loads(ep.read_text())['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())};bank={int(c):p for c,p in json.loads((B/'step_3.json').read_text())['bank'].items()};active={331,334,337,338};history=[];seen_tasks=set();total=0
for iteration in range(3):
 proof=propagate(bank,q,cap);tasks=set();links=[];changed=True
 while changed:
  changed=False
  for deletion in proof['removals']:
   cid=deletion['connection'];blocker=deletion['blocker']
   if cid not in active:continue
   group={c for c in q if q[c]['net_id']==q[blocker]['net_id']}
   if not group<=active:active.update(group);changed=True
   path=bank[cid][deletion['index']]['path'];nodeset={n for n,sw in path};conflicts=set()
   if q[cid]['net_id']!=q[blocker]['net_id']:
    for j in deletion['blocker_domain']:conflicts.update(n for n,sw in bank[blocker][j]['path'] if n in nodeset and cap[n]<2)
   if conflicts:
    links.append(dict(connection=cid,index=deletion['index'],blocker=blocker,conflict_nodes=sorted(conflicts)))
    for c in group:
     for n in conflicts:tasks.add((c,(n,)))
     tasks.add((c,tuple(sorted(conflicts))))
 searches=[];added=0
 for cid,forbidden in sorted(tasks-seen_tasks):
  seen_tasks.add((cid,forbidden));query=q[cid];value=budgets[cid]*rc.scale
  answer=search.query(query['source'],query['sink'],value.numerator//value.denominator,Counter({n:cap[n] for n in forbidden}),set(),{},1000000,sum(length.values())+1) if query['source'] not in forbidden else dict(status='SOURCE_BANNED',physical_edge_ids=None)
  event=dict(connection_id=cid,forbidden_nodes=list(forbidden),**answer);searches.append(event)
  if answer['status']!='FOUND':continue
  path=[[query['source'],None]];u=query['source']
  for eid in answer['physical_edge_ids']:source,n,sw=edge[eid];assert source==u;path.append([n,sw]);u=n
  assert not set(forbidden)&{n for n,sw in path};event['path']=path
  if not any(c['path']==path for c in bank[cid]):
   delay=F(answer['delay'],rc.scale);bank[cid].append(dict(path=path,origin='ONLINE_SUPPORT_CLOSURE_DETOUR',forbidden_nodes=list(forbidden),exact_delay_s=[delay.numerator,delay.denominator]));added+=1
 history.append(dict(iteration=iteration,active_connections=sorted(active),propagation=proof,links=links,searches=searches,new_candidates=added));total+=added;print(dict(iteration=iteration,active_connections=len(active),searches=len(searches),new_candidates=added),flush=True)
 if not added:break
p=D/'step_3.json';p.write_text(json.dumps(dict(bank={str(c):p for c,p in bank.items()},history=history),indent=2)+'\n');bindings[str(p)]=sha(p);search.close();assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,new_candidates=total,component_seconds=time.perf_counter()-start,scope='Budget-preserving support-deletion NET closure and relaxed detour searches, no target paths. No full joint/native/timing/gain conclusion.'),indent=2)+'\n')
