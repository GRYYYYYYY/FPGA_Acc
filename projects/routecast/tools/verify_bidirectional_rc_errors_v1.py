"""Direct ABI rejection preserves outputs and workspace recovers after errors."""
import ctypes as C
import json
from array import array
from pathlib import Path
from types import SimpleNamespace
from bidirectional_rc_bridge_v1 import Bidirectional
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
B=R/'experiments/bidirectional_rc_build_v1_2026-10-08/search.so'
f=dict(capacities=[1,0,1],row_offsets=[0,1,1,2],dest_ranks=[2,0])
search=Bidirectional(f,SimpleNamespace(increments=[0,1],initial=lambda u:0),B)
expected=search.search(0,2)
outputs=[C.c_uint64(123) for _ in range(4)]
stats=(C.c_uint64*4)(456,456,456,456)
search.slots[:]=array('Q',[789]*3)
def snapshot():return [x.value for x in outputs],list(stats),list(search.slots)
saved=snapshot()
statuses=[]
for source,sink,limit,weight in [(3,2,3,0),(0,1,3,0),(0,2,2,0),(0,2,3,2**63)]:
    price=array('Q',[0,0,2**63])
    status=search.lib.rc_bidi_search(search.handle,source,sink,0,weight,search.ptr(price),search.ptr(search.slots),limit,
        *[C.byref(x) for x in outputs],stats)
    assert status==(-2 if weight else -1)
    assert snapshot()==saved
    statuses.append(status)
assert search.search(0,2)==expected
badrow=array('Q',[1,1,1,2])
assert not search.lib.rc_bidi_create(3,search.ptr(badrow),*[search.ptr(a) for a in search.arrays[1:]])
bad_dest=array('Q',[3,0])
assert not search.lib.rc_bidi_create(3,search.ptr(search.arrays[0]),search.ptr(bad_dest),*[search.ptr(a) for a in search.arrays[2:]])
search.close()
paths=[Path(__file__),R/'tools/bidirectional_rc_bridge_v1.py',B,
 R/'tools/soft_demand_cpp/bidirectional_workspace_v1.cpp',R/'tools/soft_demand_cpp/tree_workspace_radix_stats_v4.cpp']
result=dict(pass_all=True,rejected_statuses=statuses,outputs_preserved=True,recovery_exact=True,
 bindings={str(p):sha(p) for p in paths})
D=R/'experiments/bidirectional_rc_errors_v1_2026-10-08';D.mkdir(exist_ok=False)
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
