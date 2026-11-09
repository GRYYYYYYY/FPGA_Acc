"""Generate new physical paths from current binary support-deletion conflicts."""
import json,time
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_bounded_wire_search_v1 import NativeBoundedSearch
from finite_route_bank_arc_consistency_v1 import propagate
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_online_direct_detours_v1_2026-10-09';D=E/'adder_online_direct_support_expand_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();vp=E/'adder_online_direct_propagation_verification_v2_2026-10-09/verification.json';doc=json.loads(vp.read_text());assert all(sha(p)==h for p,h in doc['bindings'].items());bindings={**doc['bindings'],str(vp):sha(vp),**closure([Path(__file__)])}
ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';bp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_3_budgets.json';g,h,nodes,f,rc,_=load_endpoints(ep);q={x['connection_id']:x for x in json.loads(ep.read_text())['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())};bank={int(c):opts for c,opts in json.loads((B/'step_3.json').read_text())['bank'].items()};cap=f['capacities'];length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
edge={f['edge_ids'][i]:(u,f['dest_ranks'][i],f['switch_ids'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};search=NativeBoundedSearch(rc,length);bindings.update(search.bindings);history=[];seen=set()
for iteration in range(12):
 prop=propagate(bank,q,cap);record=dict(iteration=iteration,propagation=prop,searches=[]);history.append(record)
 if prop['status']=='ARC_CONSISTENT':break
 tasks=defaultdict(set)
 for deletion in prop['removals']:
  a,i,b=deletion['connection'],deletion['index'],deletion['blocker'];path=bank[a][i]['path'];an={n for n,s in path};ap={v:(u,s) for (u,_),(v,s) in zip(path,path[1:])}
  for j in deletion['blocker_domain']:
   other=bank[b][j]['path'];bn={n for n,s in other};parents={v:(u,s) for (u,_),(v,s) in zip(other,other[1:])}
   conflicts={n for n in an&bn if cap[n]<2} if q[a]['net_id']!=q[b]['net_id'] else {n for n in ap.keys()&parents.keys() if ap[n]!=parents[n]}
   assert conflicts
   tasks[a].update(conflicts);tasks[b].update(conflicts)
 added=0
 for cid,bans in sorted(tasks.items()):
  for forbidden in sorted({(n,) for n in bans}|{tuple(sorted(bans))}):
   key=(cid,forbidden)
   if key in seen:continue
   seen.add(key);query=q[cid];value=budgets[cid]*rc.scale
   answer=dict(status='SOURCE_BANNED') if query['source'] in forbidden else search.query(query['source'],query['sink'],value.numerator//value.denominator,Counter({n:cap[n] for n in forbidden}),set(),{},1000000,sum(length.values())+1)
   event=dict(connection_id=cid,forbidden_nodes=list(forbidden),**answer);record['searches'].append(event)
   if answer['status']!='FOUND':continue
   path=[[query['source'],None]];u=query['source']
   for eid in answer['physical_edge_ids']:source,v,s=edge[eid];assert source==u;path.append([v,s]);u=v
   assert not set(forbidden)&{n for n,s in path};event['path']=path
   if not any(o['path']==path for o in bank[cid]):
    delay=F(answer['delay'],rc.scale);bank[cid].append(dict(path=path,origin='DIRECT_SUPPORT_CONFLICT_SEARCH',forbidden_nodes=list(forbidden),exact_delay_s=[delay.numerator,delay.denominator]));added+=1
 record['new_candidates']=added;print(dict(iteration=iteration,status=prop['status'],queries=len(record['searches']),added=added),flush=True)
 if not added:break
search.close();required=defaultdict(set)
for cid,opts in bank.items():
 for n in set.intersection(*[{n for n,s in o['path']} for o in opts]):required[n].add(q[cid]['net_id'])
conflicts=[dict(node=n,capacity=cap[n],required_net_ids=sorted(nets)) for n,nets in sorted(required.items()) if len(nets)>cap[n]];p=D/'step_3.json';p.write_text(json.dumps(dict(bank={str(c):opts for c,opts in bank.items()},history=history,empty_connection_ids=[],required_node_capacity_conflicts=conflicts),indent=2)+'\n')
for p in (p,ep,bp):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=[dict(step=3,candidates=sum(map(len,bank.values())),rounds=len(history),last_propagation_status=history[-1]['propagation']['status'])],component_seconds=time.perf_counter()-start,scope='Actual support-conflict candidate generation; candidates/propagation need independent verification, ARC_CONSISTENT not full feasibility. No target route paths or retry/branch traces consumed.'),indent=2)+'\n')
