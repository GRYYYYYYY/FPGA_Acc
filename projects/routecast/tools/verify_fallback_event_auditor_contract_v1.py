"""Exercise independent event auditor with nonzero recovery and tampered receipts."""
import ast,copy,hashlib,json
from pathlib import Path
from fractions import Fraction as F
from types import SimpleNamespace as NS
from collections import Counter
from buffered_rc_node_classes import arc_delay
root=Path(__file__).resolve().parents[1];source=root/'tools/verify_resident_events_actual_old_joint_fallback_v8.py'
module=ast.parse(source.read_text());functions=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in {'physical_path','union_objective','audit_fallback'}]
assert len(functions)==3
edges=[NS(source=u,sink=v,switch_id=i) for i,(u,v) in enumerate(((0,1),(0,2),(1,4),(1,5),(2,4),(2,5)))]
queries={9:dict(connection_id=9,net_id=7,source=0,sink=4),10:dict(connection_id=10,net_id=7,source=0,sink=5)}
old=[dict(queries[c],budget_integer=5,floor_integer=1,answer=dict(status='FOUND',physical_edge_ids=path,delay=delay)) for c,path,delay in ((9,[0,2],4),(10,[0,3],2))]
new=copy.deepcopy(old);new[0]['answer']=dict(status='FOUND',physical_edge_ids=[1,4],delay=2)
event=dict(status='COMMITTED',failed_connection_ids=[],primary_failed_connection_ids=[10],primary_attempts=[dict(connection_id=9,physical_edge_ids=[1,4]),dict(connection_id=10,physical_edge_ids=[1,5])],fallback=dict(status='ACCEPT_STRICT_IMPROVEMENT',old_union_cost=5,chosen_union_cost=4,search_status='OPTIMAL_WITHIN_CANDIDATES',states=5),records=new)
namespace=dict(xml=NS(graph=NS(edges=edges,nodes=[NS(capacity=1) for _ in range(6)])),classes=[(F(0),F(0))],ids=[0]*6,switches={i:(F(0),F(v)) for i,v in enumerate((1,1,3,1,1,10))},scale=1,p={'price_unit_integer':1},prices=Counter(),queries=queries,arc_delay=arc_delay)
exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),namespace)
audit=namespace['audit_fallback'];assert audit(event,old) is True
checks={'valid_nonzero_recovery':True}
for label,mutate in [
 ('wrong_old_cost',lambda e:e['fallback'].update(old_union_cost=6)),
 ('wrong_chosen_cost',lambda e:e['fallback'].update(chosen_union_cost=3)),
 ('wrong_failed_IDs',lambda e:e.update(primary_failed_connection_ids=[9])),
 ('missing_attempt',lambda e:e['primary_attempts'].pop()),
 ('false_limit',lambda e:e['fallback'].update(search_status='UNKNOWN_STATE_LIMIT',states=5)),
 ('invalid_member',lambda e:e['records'][0]['answer'].update(physical_edge_ids=[0,2],delay=4))]:
 bad=copy.deepcopy(event);mutate(bad)
 try:audit(bad,old)
 except AssertionError:checks[label]=True
 else:raise AssertionError(label)
retained=copy.deepcopy(event);retained.update(status='RETAIN_BUDGET_OR_UNREACHABLE',failed_connection_ids=[10]);retained.pop('records');retained['fallback'].update(status='RETAIN',chosen_union_cost=5,search_status='UNKNOWN_STATE_LIMIT',states=10000)
assert audit(retained,old) is False;checks['limited_retention']=True
out=root/'experiments/fallback_event_auditor_contract_v1_2026-10-09';out.mkdir(exist_ok=False)
r=dict(all_pass=True,checks=checks,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),source,root/'tools/buffered_rc_node_classes.py')},scope='Auditor nonzero/tamper synthetic fixtures. Complete online original RR event/ledger/epoch trial still required.')
(out/'verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['checks'],indent=2))
