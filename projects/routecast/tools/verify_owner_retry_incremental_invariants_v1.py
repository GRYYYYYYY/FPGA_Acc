"""Execute the frozen verifier's actual incremental statements on adversarial inventories."""
import ast,json
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];source=R/'tools/verify_adder_online_owner_retry_v2.py'
tree=ast.parse(source.read_text())
event_loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='event')
start=next(i for i,n in enumerate(event_loop.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='net' for t in n.targets))
code=compile(ast.fix_missing_locations(ast.Module(body=event_loop.body[start:],type_ignores=[])),str(source),'exec')
rows=[]
cases=[('same_net_same_parent',0,1,[(0,None),(2,7)],False),('distinct_net_capacity_one',1,1,[(0,None),(2,7)],True),('distinct_net_capacity_two',1,2,[(0,None),(2,7)],False),('same_net_conflicting_parent',0,1,[(1,None),(2,8)],True)]
for name,net,capacity,path,reject in cases:
 owners=defaultdict(set,{0:{0},2:{0}});parents=defaultdict(dict,{0:{2:(0,7)}})
 env=dict(q={10:{'net_id':net}},event={'connection_id':10,'path':path},owners=owners,parents=parents,inv=SimpleNamespace(physical=SimpleNamespace(nodes={n:('X',capacity) for n in (0,1,2)})),checked=0)
 failed=False
 try:exec(code,env)
 except AssertionError:failed=True
 assert failed==reject
 if not reject:assert env['checked']==1 and parents[net][2]==(0,7) and owners[2]==({0} if net==0 else {0,1})
 rows.append(dict(case=name,rejected=failed,expected_rejected=reject))
report=R/'experiments/adder_online_owner_retry_verification_v2_2026-10-09/verification.json';doc=json.loads(report.read_text());assert all(sha(p)==h for p,h in doc['bindings'].items());assert sum(r['generated_paths_independent_fraction_capacity_parent_pass'] for r in doc['rows'])==6176;assert sum(r['diagnostic_witnesses_fraction_owner_replay_pass'] for r in doc['rows'])==88
bindings={**closure([Path(__file__),source]),**doc['bindings'],str(report):sha(report)}
assert all(sha(p)==h for p,h in bindings.items())
D=R/'experiments/owner_retry_incremental_invariants_v1_2026-10-09';D.mkdir(exist_ok=False)
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,coverage_rows=doc['rows'],scope='Actual extracted incremental verifier statements: distinct-NET capacity and same-NET parent rejection, legal sharing and capacity-two acceptance. Positive corpus also fully rebuilt per attempt. No end-to-end performance claim.'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
