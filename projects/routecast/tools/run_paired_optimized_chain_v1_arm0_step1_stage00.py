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
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'paired_optimized_chain_v1_arm0_step1_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();bindings=closure([Path(__file__)]);roots=[]
ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';g,h,nodes,f,rc,_=load_endpoints(ep0);inv=read(g,h);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
search=NativeBoundedSearch(rc,length);bindings.update(search.bindings);edge={eid:arc for arc,eid in inv.physical.arcs.items()};rows=[]
for step in range(1,2):
 ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';bp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json';oldp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step-1}_state.json';m=json.loads(ep.read_text());q={x['connection_id']:x for x in m['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())};bank={cid:{} for cid in q};generated=[]
 def add(cid,path,origin):
  query=q[cid]
  if path[0]!=[query['source'],None] or path[-1][0]!=query['sink']:return
  assert len({n for n,s in path})==len(path);r,c=inv.classes[inv.node_classes[query['source']]];delay=r*c/2
  for (u,_),(v,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,s))==1;r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
  if delay<=budgets[cid]:bank[cid].setdefault(tuple(tuple(x) for x in path),dict(path=path,origin=origin,exact_delay_s=[delay.numerator,delay.denominator]))
 for cid,path in json.loads(oldp.read_text())['state'].items():add(int(cid),path,'OLD_ROUTE')
 empty_before=[cid for cid,candidates in bank.items() if not candidates]
 for cid in empty_before:
  query=q[cid];value=budgets[cid]*rc.scale;result=search.query(query['source'],query['sink'],value.numerator//value.denominator,Counter(),set(),{},1000000,sum(length.values())+1);generated.append(dict(connection_id=cid,**result))
  if result['status']=='FOUND':
   path=[[query['source'],None]];u=query['source']
   for eid in result['physical_edge_ids']:source,v,s=edge[eid];assert source==u;path.append([v,s]);u=v
   add(cid,path,'NEW_CAPACITY_PARENT_RELAXED_SEARCH')
 from finite_route_bank_cnf_v1 import encode
 from certified_cnf_dependency_cdcl_v2 import solve
 from independent_indexed_rup_verify_v1 import verify
 from cnf_rup_support_indexed_v1 import support
 phase_seconds=Counter();phase_calls=Counter()
 def measured(stage,fn,*args,**kwargs):
  tick=time.perf_counter()
  try:return fn(*args,**kwargs)
  finally:phase_seconds[stage]+=time.perf_counter()-tick;phase_calls[stage]+=1
 raw_encode,raw_solve,raw_verify,raw_support=encode,solve,verify,support
 encode=lambda *a,**kw:measured('encoding',raw_encode,*a,**kw)
 solve=lambda *a,**kw:measured('solver',raw_solve,*a,**kw)
 verify=lambda *a,**kw:measured('proof_model_check',raw_verify,*a,**kw)
 support=lambda *a,**kw:measured('proof_support',raw_support,*a,**kw)
 raw_query=search.query
 search.query=lambda *a,**kw:measured('detour_query',raw_query,*a,**kw)
 rounds=[];selection=None
 for iteration in range(200):
  options={cid:list(paths.values()) for cid,paths in bank.items()};cnf=encode(options,q,{n:int(cap) for n,(kind,cap) in inv.physical.nodes.items()});parentvars={i for i,role in enumerate(cnf['variables'],1) if role['kind']=='NET_PARENT'};indices=[i for i,c in enumerate(cnf['clauses']) if not any(abs(x) in parentvars for x in c)];clauses=[cnf['clauses'][i] for i in indices];result=solve(clauses,len(cnf['variables']),10000);verify(clauses,result)
  row=dict(iteration=iteration,candidates=sum(map(len,options.values())),capacity_status=result['status'],visited=result['visited_nodes']);rounds.append(row)
  if result['status']=='SAT':
   full=solve(cnf['clauses'],len(cnf['variables']),10000);verify(cnf['clauses'],full);row['full_status']=full['status']
   if full['status']=='SAT':
    terminal=D/'terminal_sat.json';terminal.write_text(json.dumps(dict(encoding=cnf,result=full),indent=2)+'\n');bindings[str(terminal)]=sha(terminal)
    selection={cid:next(i for i in range(len(opts)) if full['model'][cnf['path_vars'][f'{cid}:{i}']]) for cid,opts in options.items()};break
   if full['status']!='UNSAT':break
   clauses=cnf['clauses'];result=full;indices=list(range(len(clauses)))
  elif result['status']!='UNSAT':break
  core=support(clauses,result);roles=[cnf['variables'][abs(x)-1] for i in core for x in clauses[i]];cids=sorted({r['key'][0] for r in roles if r['kind']=='PATH'});blocked=sorted({r['key'][1] for r in roles if r['kind'] in ('NET_NODE','NET_PARENT')});row.update(core_connections=cids,core_nodes=blocked);before=sum(map(len,bank.values()));events=[]
  for cid in cids:
   query=q[cid]
   for bans in [[n] for n in blocked]+[blocked]:
    if query['source'] in bans or query['sink'] in bans:continue
    scaled=budgets[cid]*rc.scale;answer=search.query(query['source'],query['sink'],scaled.numerator//scaled.denominator,{n:f['capacities'][n] for n in bans},set(),{},1000000,sum(length.values())+1);event=dict(connection_id=cid,blocked_nodes=bans,**answer);events.append(event)
    if answer['status']=='FOUND':
     path=[[query['source'],None]];u=query['source']
     for eid in answer['physical_edge_ids']:
      source,v,s=edge[eid];assert source==u;path.append([v,s]);u=v
     assert not set(bans)&{n for n,s in path};event['path']=path;add(cid,path,'LIVE_CORE_DETOUR')
  row['new_candidates']=sum(map(len,bank.values()))-before
  artifact=D/f'round_{iteration}.json';artifact.write_text(json.dumps(dict(encoding=cnf,retained_indices=indices,proof_result=result,core_clause_indices=core,events=events),indent=2)+'\n');bindings[str(artifact)]=sha(artifact);print(row,flush=True)
  if row['new_candidates']==0:break
 search.close();options={cid:list(paths.values()) for cid,paths in bank.items()};out=dict(bank=options,selection=selection,paths={c:options[c][i]['path'] for c,i in selection.items()} if selection else None,rounds=rounds);p=D/'result.json';p.write_text(json.dumps(out,indent=2)+'\n');bindings[str(p)]=sha(p)
 for path in (ep,bp,oldp):bindings[str(path)]=sha(path)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,status='FOUND_REQUIRES_INDEPENDENT_FULL_GATES' if selection else 'NO_COMPLETE_SELECTION',component_seconds=time.perf_counter()-start,phase_seconds=dict(phase_seconds),phase_calls=dict(phase_calls),scope='Fresh oldstate/endpoints/budget generation including graph setup, per-demand queries, capacity/fullCNF solve, RUP replay, support extraction and detours. No archived candidate banks or target paths. Native/canonical/quality and external wallclock comparison pending.'),indent=2)+'\n');print(out['rounds'][-1],flush=True)
