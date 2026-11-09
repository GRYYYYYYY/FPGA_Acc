"""Synthetic parent-conflict and cross-NET capacity tests."""
from types import SimpleNamespace
from pathlib import Path
import json,hashlib
from actual_change_physical_delta_v1_2026_10_18 import PhysicalDelta
R=Path(__file__).resolve().parents[1];D=R/'experiments/physical_delta_conflicts_v1_2026-10-18';D.mkdir(exist_ok=False)
nodes={0:('SOURCE','1'),1:('CHANX','1'),2:('SINK','1'),3:('SINK','1'),4:('CHANY','1'),5:('SOURCE','1'),6:('SINK','1'),7:('CHANX','1')}
arcs={k:i for i,k in enumerate([(0,1,0),(1,2,0),(1,3,0),(0,4,0),(1,4,0),(4,2,0),(4,3,0),(5,4,0),(4,6,0),(5,7,0),(7,6,0)])};inv=SimpleNamespace(digest='fixture',physical=SimpleNamespace(nodes=nodes,arcs=arcs,switches={0}))
q={0:dict(net_id=0,source=0,sink=2),1:dict(net_id=0,source=0,sink=3),2:dict(net_id=1,source=5,sink=6)};old={0:((0,None),(1,0),(2,0)),1:((0,None),(1,0),(3,0)),2:((5,None),(4,0),(6,0))};state=PhysicalDelta(old,q,inv);snapshot=dict(state.occupancy)
conflict={**old,0:((0,None),(1,0),(4,0),(2,0)),1:((0,None),(4,0),(3,0))}
try:state.evaluate(conflict,q,inv)
except ValueError as e:assert str(e)=='Conflicting NET parents'
else:raise AssertionError('Conflicting parents accepted')
assert dict(state.occupancy)==snapshot
new={**old,0:((0,None),(4,0),(2,0)),1:((0,None),(4,0),(3,0))};answer=state.evaluate(new,q,inv);assert answer['node_occupancy']['4']==2 and answer['overflow_units']==1
# Simultaneous owner removal: final state legal despite temporary overlap if updates serialized.
new[2]=((5,None),(7,0),(6,0));answer=state.evaluate(new,q,inv);assert answer['node_occupancy']['4']==1 and answer['overflow_units']==0;assert dict(state.occupancy)==snapshot
paths=[Path(__file__),R/'tools/actual_change_physical_delta_v1_2026_10_18.py'];bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,conflicting_parent_rejected=True,cross_net_overflow_detected=True,simultaneous_owner_transfer_final_occupancy_correct=True,old_state_unchanged=True,scope='Synthetic structural/capacity contract, not native full acceptance or timing evidence.'),f,indent=2);f.write('\n')
print('PASS parent conflict, interNET overflow, owner transfer, immutable old state')
