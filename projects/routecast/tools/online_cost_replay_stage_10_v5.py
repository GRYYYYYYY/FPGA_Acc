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
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'online_cost_replay_v5_adder_online_detour_bank_v1_2026-10-09';D=E/'online_cost_replay_v5_adder_online_proof_expand_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();vp=E/'online_cost_replay_v5_adder_online_bank_joint_verification_v1_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';g,h,nodes,f,rc,_=load_endpoints(ep0);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
edge={f['edge_ids'][i]:(u,f['dest_ranks'][i],f['switch_ids'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};search=NativeBoundedSearch(rc,length);bindings.update(search.bindings);cap=f['capacities'];rows=[]
for step in range(1,4):
 ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';bp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json';q={x['connection_id']:x for x in json.loads(ep.read_text())['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())};bank={int(c):p for c,p in json.loads((B/f'step_{step}.json').read_text())['bank'].items()};history=[];totalnew=0
 for iteration in range(5):
  result=solve(bank,q,cap,max_nodes=100000);rounddata=dict(iteration=iteration,result=result,searches=[]);history.append(rounddata)
  if result['status']!='FINITE_BANK_EXHAUSTED' or iteration==4:break
  selection={};proof=result['proof']
  while True:
   selection.update(proof['forced'])
   if proof['kind']=='DEAD':break
   child=proof['children'][0];selection[proof['connection']]=child['index'];proof=child['proof']
  failed=proof['empty_connection'];owners=defaultdict(set);owner_cids=defaultdict(set)
  for cid,index in selection.items():
   for n,s in bank[cid][index]['path']:owners[n].add(q[cid]['net_id']);owner_cids[n].add(cid)
  conflicts=set()
  for candidate in bank[failed]:
   for n,s in candidate['path']:
    if len(owners[n]|{q[failed]['net_id']})>cap[n]:conflicts.add(n)
  tasks={(failed,tuple(sorted(conflicts)))} if conflicts else set()
  for n in conflicts:
   for cid in owner_cids[n]:
    if q[cid]['net_id']!=q[failed]['net_id']:tasks.add((cid,(n,)))
  added=0;rounddata.update(failed_connection=failed,conflict_nodes=sorted(conflicts))
  for cid,forbidden in sorted(tasks):
   query=q[cid];value=budgets[cid]*rc.scale
   if query['source'] in forbidden:answer=dict(status='SOURCE_BANNED',physical_edge_ids=None)
   else:answer=search.query(query['source'],query['sink'],value.numerator//value.denominator,Counter({n:cap[n] for n in forbidden}),set(),{},1000000,sum(length.values())+1)
   event=dict(connection_id=cid,forbidden_nodes=list(forbidden),**answer);rounddata['searches'].append(event)
   if answer['status']!='FOUND':continue
   path=[[query['source'],None]];u=query['source']
   for eid in answer['physical_edge_ids']:source,n,s=edge[eid];assert source==u;path.append([n,s]);u=n
   assert not ({n for n,s in path}&set(forbidden));event['path']=path
   if not any(c['path']==path for c in bank[cid]):
    delay=F(answer['delay'],rc.scale);bank[cid].append(dict(path=path,origin='ONLINE_JOINT_PROOF_DETOUR',forbidden_nodes=list(forbidden),exact_delay_s=[delay.numerator,delay.denominator]));added+=1
  totalnew+=added;rounddata['new_candidates']=added
  if not added:break
 out=dict(bank={str(c):p for c,p in bank.items()},history=history,status=result['status'],selection=result['selection']);p=D/f'step_{step}.json';p.write_text(json.dumps(out,indent=2)+'\n');bindings[str(p)]=sha(p);row=dict(step=step,rounds=len(history),new_candidates=totalnew,status=result['status'],candidates=sum(map(len,bank.values())));rows.append(row);print(row,flush=True)
search.close();assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='Proof-guided online bank expansion, explicit unchanged target-derived model budgets. Selection/proofs require independent replay. No target paths consumed, native acceptance/independent timing/gain claim.'),indent=2)+'\n')
