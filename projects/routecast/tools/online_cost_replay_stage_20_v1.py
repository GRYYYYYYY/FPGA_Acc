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
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'online_cost_replay_v1_adder_online_small_component_detours_v1_2026-10-09';D=E/'online_cost_replay_v1_adder_online_owner337_detours_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();vp=E/'online_cost_replay_v1_adder_online_component_verification_v2_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';g,h,nodes,f,rc,_=load_endpoints(ep0);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
edge={f['edge_ids'][i]:(u,f['dest_ranks'][i],f['switch_ids'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};search=NativeBoundedSearch(rc,length);bindings.update(search.bindings);cap=f['capacities'];rows=[]
step=3;ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';bp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_3_budgets.json';q={x['connection_id']:x for x in json.loads(ep.read_text())['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())};bank={int(c):p for c,p in json.loads((B/'step_3.json').read_text())['bank'].items()};domains=json.loads((E/'online_cost_replay_v1_adder_online_bank_propagation_v1_2026-10-09/step_3.json').read_text())['propagation']['domains'];cids=[331,334,337,338];local={c:list(bank[c]) for c in cids};attempts=[];added=0
for cid in cids:
 for forbidden in ([[872],[864,872],[868,872],[864,868,872]] if cid==337 else [[864,868,872]]):
  query=q[cid];value=budgets[cid]*rc.scale;answer=search.query(query['source'],query['sink'],value.numerator//value.denominator,Counter({n:cap[n] for n in forbidden}),set(),{},1000000,sum(length.values())+1);event=dict(connection_id=cid,forbidden_nodes=forbidden,**answer);attempts.append(event)
  if answer['status']!='FOUND':continue
  path=[[query['source'],None]];u=query['source']
  for eid in answer['physical_edge_ids']:source,n,sw=edge[eid];assert source==u;path.append([n,sw]);u=n
  assert not set(forbidden)&{n for n,sw in path};event['path']=path;delay=F(answer['delay'],rc.scale);candidate=dict(path=path,origin='ONLINE_SMALL_COMPONENT_DETOUR',forbidden_nodes=forbidden,exact_delay_s=[delay.numerator,delay.denominator])
  if not any(c['path']==path for c in bank[cid]):bank[cid].append(candidate);added+=1
  if not any(c['path']==path for c in local[cid]):local[cid].append(candidate)
result=solve(local,q,cap,max_nodes=100000);out=dict(bank={str(c):p for c,p in bank.items()},local_bank={str(c):p for c,p in local.items()},attempts=attempts,local_result=result);p=D/'step_3.json';p.write_text(json.dumps(out,indent=2)+'\n');bindings[str(p)]=sha(p);search.close();assert all(sha(p)==h for p,h in bindings.items());row=dict(step=3,new_candidates=added,status_counts=dict(Counter(x['status'] for x in attempts)),local_joint_status=result['status'],visited_nodes=result['visited_nodes']);(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=[row],component_seconds=time.perf_counter()-start,scope='Targeted three-demand component detours under unchanged explicit model budgets. Local selection is not full516 route, no target paths/native/timing/gain claim.'),indent=2)+'\n');print(row,flush=True)
