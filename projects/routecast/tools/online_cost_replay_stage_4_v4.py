"""Online trace-derived candidates plus new independent demand searches; no target paths."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_bounded_wire_search_v1 import NativeBoundedSearch
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'online_cost_replay_v4_adder_online_candidate_bank_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();bindings=closure([Path(__file__)]);roots=[]
for stem in ('online_cost_replay_v4_adder_online_owner_retry','online_cost_replay_v4_adder_online_conflict_branch'):
 root=E/(stem+'_v1_2026-10-09');proof=E/(stem+'_verification_v1_2026-10-09/verification.json');v=json.loads(proof.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(proof)]=sha(proof);roots.append(root)
ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';g,h,nodes,f,rc,_=load_endpoints(ep0);inv=read(g,h);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
search=NativeBoundedSearch(rc,length);bindings.update(search.bindings);edge={eid:arc for arc,eid in inv.physical.arcs.items()};rows=[]
for step in range(1,4):
 ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';bp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json';oldp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step-1}_state.json';m=json.loads(ep.read_text());q={x['connection_id']:x for x in m['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())};bank={cid:{} for cid in q};generated=[]
 def add(cid,path,origin):
  query=q[cid]
  if path[0]!=[query['source'],None] or path[-1][0]!=query['sink']:return
  assert len({n for n,s in path})==len(path);r,c=inv.classes[inv.node_classes[query['source']]];delay=r*c/2
  for (u,_),(v,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,s))==1;r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
  if delay<=budgets[cid]:bank[cid].setdefault(tuple(tuple(x) for x in path),dict(path=path,origin=origin,exact_delay_s=[delay.numerator,delay.denominator]))
 for cid,path in json.loads(oldp.read_text())['state'].items():add(int(cid),path,'OLD_ROUTE')
 for root in roots:
  doc=json.loads((root/f'step_{step}.json').read_text())
  for attempt in doc['attempts']:
   for event in attempt['events']+[attempt.get('capacity_relaxed_witness',{})]:
    if event.get('status')=='FOUND':add(event['connection_id'],event['path'],root.name)
 empty_before=[cid for cid,candidates in bank.items() if not candidates]
 for cid in empty_before:
  query=q[cid];value=budgets[cid]*rc.scale;result=search.query(query['source'],query['sink'],value.numerator//value.denominator,Counter(),set(),{},1000000,sum(length.values())+1);generated.append(dict(connection_id=cid,**result))
  if result['status']=='FOUND':
   path=[[query['source'],None]];u=query['source']
   for eid in result['physical_edge_ids']:source,v,s=edge[eid];assert source==u;path.append([v,s]);u=v
   add(cid,path,'NEW_CAPACITY_PARENT_RELAXED_SEARCH')
 necessary=defaultdict(set);empty=[]
 for cid,candidates in bank.items():
  if not candidates:empty.append(cid);continue
  for node in set.intersection(*[{n for n,s in path} for path in candidates]):necessary[node].add(q[cid]['net_id'])
 conflicts=[dict(node=n,capacity=int(inv.physical.nodes[n][1]),required_net_ids=sorted(nets)) for n,nets in sorted(necessary.items()) if len(nets)>int(inv.physical.nodes[n][1])]
 out=dict(bank={str(cid):list(candidates.values()) for cid,candidates in bank.items()},empty_before_new_search=empty_before,new_searches=generated,empty_connection_ids=empty,required_node_capacity_conflicts=conflicts);p=D/f'step_{step}.json';p.write_text(json.dumps(out,indent=2)+'\n')
 for path in (ep,bp,oldp,p):bindings[str(path)]=sha(path)
 row=dict(step=step,candidates=sum(map(len,bank.values())),missing_before_new_search=len(empty_before),missing_after=len(empty),necessary_capacity_conflicts=len(conflicts),finite_bank_infeasible=bool(empty or conflicts));rows.append(row);print(row,flush=True)
search.close();assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='Finite bank from online-produced paths, old routes and new per-demand relaxed searches; all eligible exact model budget paths. No target paths consumed. Only finite-bank necessary conflicts, no global infeasibility, joint candidate/native/timing/speedup claim.'),indent=2)+'\n')
