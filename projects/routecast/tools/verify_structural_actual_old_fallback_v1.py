"""Shared trunk counted once; structural objective does not enter raw budgets."""
import sys,json
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from structural_actual_old_fallback_adapter_v1 import fallback
from pre_route_endpoints import sha
f=dict(row_offsets=[0,2,4,6,6,6],dest_ranks=[1,2,3,4,3,4],edge_ids=list(range(6)),capacities=[1]*5)
inc=[1]*6;rc=SimpleNamespace(initial=lambda u:0,increment=lambda slot:inc[slot],path=lambda source,sink,path:sum(inc[e] for e in path))
qs=[dict(connection_id=0,net_id=0,source=0,sink=3),dict(connection_id=1,net_id=0,source=0,sink=4)]
old=[dict(q,answer=dict(status='FOUND',physical_edge_ids=[0,2+i],delay=2),budget_integer=2,floor_integer=2) for i,q in enumerate(qs)]
parents={2:(0,1),3:(2,4),4:(2,5)};base=[0,10,0,0,0]
v=fallback(f,rc,{i:i for i in range(6)},qs,old,parents,{3,4},{},0,base)
assert v['status']=='ACCEPT_STRICT_IMPROVEMENT' and v['old_union_cost']==13 and v['chosen_union_cost']==3
assert all(x['answer']['delay']==x['budget_integer']==2 for x in v['records'])
assert [x['answer']['physical_edge_ids'] for x in v['records']]==[[1,4],[1,5]]
# A congestion penalty on the alternate trunk prevents structural improvement.
w=fallback(f,rc,{i:i for i in range(6)},qs,old,parents,{3,4},{2:20},1,base)
assert w['status']=='RETAIN' and w['chosen_union_cost']==w['old_union_cost']==13
O=R/'experiments/structural_actual_old_fallback_contract_v1_2026-10-10';O.mkdir(exist_ok=True)
(O/'verification.json').write_text(json.dumps(dict(bindings=closure([Path(__file__)]),shared_trunk_static_cost_charged_once=True,exact_raw_budget_preserved=True,price_times_weight_and_base_compete_in_same_union_objective=True,accept=v,retain=w,scope='Targeted adapter fixtures with independent hand-computed union objectives; original bounded joint search unchanged. Not full randomized/native/realgraph feedback evidence.'),indent=2)+'\n')
print('STRUCTURAL FALLBACK ADAPTER PASS')
