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
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'paired_history_chain_v1_arm0_step3_stage_1_2026-10-09';D.mkdir(exist_ok=False)
start=time.perf_counter();bindings=closure([Path(__file__)])
source=E/'paired_history_chain_v1_arm0_step3_stage_0_2026-10-09'
for name in ('verification.json','independent_verification.json','result.json'):
 p=source/name;bindings[str(p)]=sha(p)
 receipt=json.loads(p.read_text())
 for filename,digest in receipt.get('bindings',{}).items():assert sha(filename)==digest;bindings[filename]=digest
base=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json'
g=R/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits/rr_graph.xml'
ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json'
bp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_3_budgets.json'
op=E/'paired_history_chain_v1_arm0_step2_stage_2_2026-10-09/result.json'
previous_quality=E/'paired_history_chain_v1_arm0_step2_stage_6_2026-10-09/verification.json'
previous=json.loads(previous_quality.read_text());assert all(sha(p)==h for p,h in previous['bindings'].items())
assert previous['rows'][0]['step']==2 and previous['rows'][0]['full_named_paths_preserved']
bindings[str(previous_quality)]=sha(previous_quality)

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
for cid,path in json.loads(op.read_text())['paths'].items():add(int(cid),path,'ELIGIBLE_ACTUAL_OLD_ROUTE')
for attempt in json.loads((source/'result.json').read_text())['attempts']:
 for cid,path in attempt['paths'].items():add(int(cid),path,'ACTUAL_PARTIAL_SELECTION')
 for i,event in enumerate(attempt['events']):
  if event['status']!='FOUND':continue
  cid=event['cid'];path=[[q[cid]['source'],None]]
  for eid in event['physical_edge_ids']:
   u,v,s=edge[eid];assert u==path[-1][0];path.append([v,s])
  add(cid,path,dict(event=i))
bank={cid:list(options.values()) for cid,options in bank.items()}
encoding=encode(bank,q,{n:int(cap) for n,(_,cap) in inv.physical.nodes.items()})
print(dict(candidates=sum(map(len,bank.values())),empty_cids=[cid for cid,x in bank.items() if not x],variables=len(encoding['variables']),clauses=len(encoding['clauses'])),flush=True)
tick=time.perf_counter();result=solve(encoding['clauses'],len(encoding['variables']),10000);solver_seconds=time.perf_counter()-tick
verify(encoding['clauses'],result)
paths=None
if result['status']=='SAT':
 paths={cid:next(option['path'] for i,option in enumerate(options) if result['model'][encoding['path_vars'][f'{cid}:{i}']]) for cid,options in bank.items()}
p=D/'result.json';p.write_text(json.dumps(dict(bank=bank,encoding=encoding,result=result,paths=paths),indent=2)+'\n');bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,status=result['status'],solver_seconds=solver_seconds,component_seconds=time.perf_counter()-start,scope='Retrospective actual search-event bank selection. SAT/UNSAT covers finite bank only. Independent structural/RUP/full path and native/canonical gates pending. Archived search production time excluded; no online cost claim.'),indent=2)+'\n')
print(dict(status=result['status'],visited=result['visited_nodes'],solver_seconds=solver_seconds),flush=True)
