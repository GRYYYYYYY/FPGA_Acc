"""Retrospective joint selection of actual history-search paths; not online timing."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from finite_route_bank_cnf_v1 import encode
from certified_cnf_dependency_cdcl_v2 import solve
from independent_indexed_rup_verify_v1 import verify
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'fresh_history_workflow_v1_stage_2_2026-10-09';D.mkdir(exist_ok=False)
start=time.perf_counter();bindings=closure([Path(__file__)])
source=E/'fresh_history_workflow_v1_stage_0_2026-10-09'
for name in ('verification.json','independent_verification.json','result.json'):
 p=source/name;bindings[str(p)]=sha(p)
 receipt=json.loads(p.read_text())
 for filename,digest in receipt.get('bindings',{}).items():assert sha(filename)==digest;bindings[filename]=digest
base=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json'
g=R/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits/rr_graph.xml'
ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json'
bp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_1_budgets.json'
op=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_0_state.json'
for p in (g,ep,bp,op):bindings[str(p)]=sha(p)
inv=read(g,sha(g));edge={eid:arc for arc,eid in inv.physical.arcs.items()}
q={x['connection_id']:x for x in json.loads(ep.read_text())['connections']}
budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())}
bank={cid:{} for cid in q}
def add(cid,path,origin):
 if path[0]!=[q[cid]['source'],None] or path[-1][0]!=q[cid]['sink']:return
 assert len({n for n,s in path})==len(path)
 r,c=inv.classes[inv.node_classes[path[0][0]]];delay=r*c/2
 for (u,_),(v,s) in zip(path,path[1:]):
  assert inv.arc_multiplicities.get((u,v,s))==1
  r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
 if delay<=budgets[cid]:bank[cid].setdefault(tuple(tuple(x) for x in path),dict(path=path,origin=origin))
from collections import Counter
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_bounded_wire_search_v1 import NativeBoundedSearch
from cnf_rup_support_indexed_v1 import support
prior=E/'fresh_history_workflow_v1_stage_1_2026-10-09'
for name in ('verification.json','independent_verification.json','result.json'):
 p=prior/name;bindings[str(p)]=sha(p)
 for filename,digest in json.loads(p.read_text()).get('bindings',{}).items():assert sha(filename)==digest;bindings[filename]=digest
for cid,options in json.loads((prior/'result.json').read_text())['bank'].items():
 for option in options:add(int(cid),option['path'],'AUTHENTICATED_HISTORY_BANK')
_,_,nodes,fields,rc,_=load_endpoints(base);bindings[str(base)]=sha(base);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
search=NativeBoundedSearch(rc,length);bindings.update(search.bindings)
rounds=[];solver_seconds=0.;paths=None
for iteration in range(64):
 options={cid:list(opts.values()) for cid,opts in bank.items()}
 encoding=encode(options,q,{n:int(cap) for n,(_,cap) in inv.physical.nodes.items()})
 tick=time.perf_counter();result=solve(encoding['clauses'],len(encoding['variables']),10000);solver_seconds+=time.perf_counter()-tick
 verify(encoding['clauses'],result)
 row=dict(iteration=iteration,candidates=sum(map(len,options.values())),encoding=encoding,result=result,events=[])
 rounds.append(row)
 if result['status']=='SAT':
  paths={cid:next(option['path'] for i,option in enumerate(opts) if result['model'][encoding['path_vars'][f'{cid}:{i}']]) for cid,opts in options.items()};break
 if result['status']!='UNSAT':break
 core=support(encoding['clauses'],result);row['core_clause_indices']=core
 roles=[encoding['variables'][abs(lit)-1] for index in core for lit in encoding['clauses'][index]]
 cids=sorted({r['key'][0] for r in roles if r['kind']=='PATH'});blocked=sorted({r['key'][1] for r in roles if r['kind'] in ('NET_NODE','NET_PARENT')})
 before=sum(map(len,bank.values()))
 for cid in cids:
  for bans in [[n] for n in blocked]+[blocked]:
   if q[cid]['source'] in bans or q[cid]['sink'] in bans:continue
   scaled=budgets[cid]*rc.scale
   answer=search.query(q[cid]['source'],q[cid]['sink'],scaled.numerator//scaled.denominator,Counter({n:int(inv.physical.nodes[n][1]) for n in bans}),set(),{},100000,sum(length.values())+1)
   event=dict(cid=cid,blocked_nodes=bans,**answer);row['events'].append(event)
   if answer['status']=='FOUND':
    path=[[q[cid]['source'],None]]
    for eid in answer['physical_edge_ids']:
     u,v,s=edge[eid];assert u==path[-1][0];path.append([v,s])
    assert not set(bans)&{n for n,s in path};event['path']=path;add(cid,path,dict(iteration=iteration,blocked_nodes=bans))
 row['new_candidates']=sum(map(len,bank.values()))-before
 print(dict(iteration=iteration,status=result['status'],new_candidates=row['new_candidates'],core_cids=cids),flush=True)
 if not row['new_candidates']:break
search.close();bank={cid:list(opts.values()) for cid,opts in bank.items()}
p=D/'result.json';p.write_text(json.dumps(dict(bank=bank,encoding=encoding,result=result,paths=paths,rounds=rounds),indent=2)+'\n');bindings[str(p)]=sha(p)
assert all(sha(p)==digest for p,digest in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,status=result['status'],solver_seconds=solver_seconds,component_seconds=time.perf_counter()-start,scope='Retrospective authenticated history warmbank plus up to64 proof-supported detour rounds;100000labels/query. No fresh workflow timing or native acceptance claim; bank UNSAT only.'),indent=2)+'\n')
print(dict(status=result['status'],rounds=len(rounds),candidates=sum(map(len,bank.values())),component_seconds=time.perf_counter()-start),flush=True)
