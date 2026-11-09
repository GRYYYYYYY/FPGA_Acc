"""Old-state plus explicit budget search; target route/state is never consumed."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
from class_cached_rc_endpoint_context_v1 import load_endpoints
from transaction_shared_tree_ledger_v1 import TransactionLedger
from native_bounded_wire_search_v1 import NativeBoundedSearch
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'online_cost_replay_v1_adder_online_owner_retry_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';g,h,nodes,f,rc,_=load_endpoints(ep0);bindings=closure([Path(__file__)]);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
search=NativeBoundedSearch(rc,length);bindings.update(search.bindings);bindings[str(g)]=h;edge={f['edge_ids'][i]:(u,f['dest_ranks'][i],f['switch_ids'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};lookup={v:k for k,v in edge.items()};rows=[]
for step in range(1,4):
 oldep=ep0 if step==1 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step-1}_endpoints.json';ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';oldp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step-1}_state.json';bp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json'
 for p in (oldep,ep,oldp,bp):bindings[str(p)]=sha(p)
 om=json.loads(oldep.read_text());m=json.loads(ep.read_text());assert om['graph_sha256']==m['graph_sha256']==h;assert all(sha(x['path'])==x['sha256'] for meta in (om,m) for x in meta['inputs'].values());oq={q['connection_id']:q for q in om['connections']};q={q['connection_id']:q for q in m['connections']};old={int(c):tuple(tuple(x) for x in p) for c,p in json.loads(oldp.read_text())['state'].items()};budgets={b['connection_id']:F(*b['exact_delay_s']) for b in json.loads(bp.read_text())};assert set(old)==set(q)==set(oq)==set(budgets)
 changed={c for c in q if (oq[c]['source'],oq[c]['sink'])!=(q[c]['source'],q[c]['sink'])};budgetfails=set()
 for c in set(q)-changed:
  path=old[c];ids=[lookup[u,v,s] for (u,_),(v,s) in zip(path,path[1:])]
  if F(rc.path(q[c]['source'],q[c]['sink'],ids),rc.scale)>budgets[c]:budgetfails.add(c)
 nets={q[c]['net_id'] for c in changed|budgetfails};order=sorted(nets);seen=set();attempts=[];stop='MAX_RETRIES'
 for retry in range(32):
  signature=(tuple(sorted(nets)),tuple(order))
  if signature in seen:stop='REPEATED_RELEASE_ORDER';break
  seen.add(signature)
  released=sorted(c for c in q if q[c]['net_id'] in nets);candidate=TransactionLedger(old,oq,f['capacities'],length)
  for cid in released:candidate.release(cid)
  candidate.queries=q;events=[];failed=None
  for net in order:
   for cid in sorted((c for c in released if q[c]['net_id']==net),key=lambda c:(budgets[c],c)):
    query=q[cid];kept=set(candidate.nodes[net]);parents=dict(candidate.parents[net]);outside=Counter({n:v-int(n in candidate.nodes[net]) for n,v in candidate.occupancy.items()});value=budgets[cid]*rc.scale
    result=search.query(query['source'],query['sink'],value.numerator//value.denominator,outside,kept,parents,1000000,sum(length.values())+1);event=dict(connection_id=cid,**result)
    if result['status']!='FOUND':failed=cid;events.append(event);break
    path=[(query['source'],None)];u=query['source']
    for eid in result['physical_edge_ids']:
     source,v,s=edge[eid];assert source==u;path.append((v,s));u=v
    candidate.insert(cid,path);event['path']=path;events.append(event)
   if failed is not None:break
  attempt=dict(retry=retry,released_nets=sorted(nets),order=list(order),events=events,failed_connection=failed);attempts.append(attempt)
  if failed is None:stop='CANDIDATE_COMPLETE';break
  query=q[failed];net=query['net_id'];value=budgets[failed]*rc.scale
  witness=search.query(query['source'],query['sink'],value.numerator//value.denominator,Counter(),kept,parents,1000000,sum(length.values())+1);attempt['capacity_relaxed_witness']=dict(connection_id=failed,**witness)
  if witness['status']!='FOUND':stop='CAPACITY_RELAXATION_NOT_FOUND';break
  path=[(query['source'],None)];u=query['source'];external=set();internal=set()
  for eid in witness['physical_edge_ids']:
   source,v,sw=edge[eid];assert source==u;path.append((v,sw));u=v
   if outside[v]>=f['capacities'][v]:
    owners={n for n,used in candidate.nodes.items() if v in used and n!=net};external.update(owners-nets);internal.update(owners&nets)
  attempt['capacity_relaxed_witness'].update(path=path,external_old_nets=sorted(external),already_staged_nets=sorted(internal))
  if external:
   nets.update(external);order=[net]+sorted(nets-{net});attempt['action']='EXPAND_EXTERNAL_AND_PRIORITIZE_FAILED'
  elif internal:
   order=[net]+[n for n in order if n!=net];attempt['action']='PRIORITIZE_FAILED_NET'
  else:stop='NO_CAPACITY_OWNER_ACTION';break
 success=failed is None
 if success:
  assert len(candidate.state)==516 and all(candidate.state[c]==old[c] for c in set(q)-set(released));state={str(c):p for c,p in candidate.state.items()}
 else:state=None
 out=dict(step=step,endpoint_changed=len(changed),retained_budget_failure_connections=len(budgetfails),released_connections=len(released),released_nets=len(nets),attempts=attempts,stop_reason=stop,events=events,committed=success,failed_connection=failed,state=state,old_state_unchanged=True)
 p=D/f'step_{step}.json';p.write_text(json.dumps(out,indent=2)+'\n');bindings[str(p)]=sha(p);rows.append({k:v for k,v in out.items() if k not in ('events','state','attempts')});print(rows[-1],flush=True)
search.close();assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='Bounded dynamic owner-release and failed-NET-priority online retries, no target route/state/prediction consumed; old state supplied per transition and explicit target-derived budgets. Broad wire allowance, no quality/nonregression/native/independent timing/speedup claim; failed search is not infeasibility proof.'),indent=2)+'\n')
