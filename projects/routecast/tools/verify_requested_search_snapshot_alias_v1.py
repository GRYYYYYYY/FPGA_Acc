"""Borrowed production Parents views cannot corrupt detached requested paths."""
import json,sys
from pathlib import Path
from array import array
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from soft_demand_cpp_bridge_v1 import Parents
from freeze_requested_search_result_v1 import freeze_requested
from source_binding_v2 import closure
raw=array('Q',[7,20,30,40]);nodes=array('Q',[(1<<64)-1,0,1,1]);slots=array('Q',[0,101,102,103]);borrowed=Parents(nodes,slots)
frozen=freeze_requested(0,{2,3},raw,borrowed,{2,3})
assert frozen==({0:7,2:30,3:40},{1:(0,101),2:(1,102),3:(1,103)},frozenset({2,3}))
raw[:]=array('Q',[99]*4);nodes[:]=array('Q',[(1<<64)-1]*4);slots[:]=array('Q',[900]*4)
assert frozen==({0:7,2:30,3:40},{1:(0,101),2:(1,102),3:(1,103)},frozenset({2,3}))
assert freeze_requested(0,{0},raw,borrowed,{0})==({0:99},{},frozenset({0}))
assert freeze_requested(0,{2},{},{},set())==({},{},frozenset())
rejected=[]
for label,args in [('cycle',(0,{2},raw,{2:(1,2),1:(2,1)},{2})),('nonrequested',(0,{2},raw,{}, {3})),('missing_parent',(0,{2},raw,{}, {2}))]:
 try:freeze_requested(*args)
 except (ValueError,KeyError):rejected.append(label)
 else:raise AssertionError(label)
D=R/'experiments/requested_search_snapshot_alias_v1_2026-10-10';D.mkdir()
(D/'verification.json').write_text(json.dumps(dict(bindings=closure([Path(__file__)]),borrowed_real_Parents_view_reuse_does_not_change_requested_snapshot=True,shared_trunk_source_target_and_unsettled_cases_pass=True,rejected=rejected,scope='Requested-output ownership safety using production borrowed Parents view over mutable arrays. No C++ concurrent workspace safety, full graph/path equivalence, batching performance or full workflow gain proof.'),indent=2)+'\n')
print('PASS requested-path snapshot ownership and rejection',rejected)
