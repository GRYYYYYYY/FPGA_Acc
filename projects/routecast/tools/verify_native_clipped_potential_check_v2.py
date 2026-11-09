"""Overflow, clipping, tamper rejection and exact Python fallback checks."""
import json
from array import array
from collections import Counter
from pathlib import Path
from native_clipped_potential_check_v2 import PotentialCheck,MAX
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
fixture=R/'tools/verify_native_minrc_certificate_boundaries_v4_retry.py'
s=fixture.read_text();exec(s[s.index('class RC:'):s.index('cases=')])
D=R/'experiments/native_clipped_potential_check_v2_2026-10-08';D.mkdir(exist_ok=False)
bindings={str(Path(__file__)):sha(Path(__file__)),str(fixture):sha(fixture),str(R/'tools/native_clipped_potential_check_v2.py'):sha(R/'tools/native_clipped_potential_check_v2.py')};rows=[]
for name,initial,weight,clip,pot in [
 ('normal',0,1,2,{0:0,1:1}),('maxclip',MAX-1,2,MAX+1,{0:MAX-1}),
 ('large_fallback',MAX+1,1,MAX+3,{0:MAX+1,1:MAX+2}),
 ('large_increment',0,MAX+1,MAX+2,{0:0,1:MAX+1}),
 ('zero_clip',0,0,0,{})]:
 rc=RC(initial,[[(1,weight)],[]]);checker=PotentialCheck(rc);bindings.update(checker.bindings)
 count=checker.check(0,clip,pot,Counter(),{})
 assert count==(1 if pot else 0)
 rows.append(dict(case=name,checks=count,native_calls=checker.native_calls,fallback_calls=checker.fallback_calls))
rc=RC(0,[[(1,1)],[]]);checker=PotentialCheck(rc);rejected=[]
for name,clip,pot in [('source',2,{0:1,1:1}),('arc',3,{0:0,1:2}),('range',2,{0:0,1:2}),('negative',2,{0:0,1:-1})]:
 try:checker.check(0,clip,pot,Counter(),{})
 except ValueError:rejected.append(name)
 else:raise AssertionError(name)
assert checker.check(0,3,{0:0,1:2},Counter({1:MAX+100}),{})==0
assert checker.check(0,3,{0:0,1:2},Counter(),{1:(1,0)})==0
assert checker.check(0,2,{0:0,1:1},Counter(),{})==1
scratch_identity=[a.buffer_info() for a in checker.scratch]
for i in range(20):
 assert checker.check(0,3,{0:0,1:2},Counter({1:1}),{})==0
 try:checker.check(0,3,{0:0,1:2},Counter(),{})
 except ValueError:pass
 else:raise AssertionError('Stale occupancy accepted invalid potential')
 assert checker.check(0,3,{0:0,1:2},Counter(),{1:(1,0)})==0
 try:checker.check(0,3,{0:0,1:2},Counter(),{})
 except ValueError:pass
 else:raise AssertionError('Stale parent accepted invalid potential')
 assert checker.check(0,2,{0:0,1:1},Counter(),{})==1
 assert checker.check(0,0,{},Counter(),{})==0
 assert checker.check(0,2,{0:0,1:1},Counter(),{})==1
assert scratch_identity==[a.buffer_info() for a in checker.scratch]
original=rc.fields['dest_ranks'];rc.fields['dest_ranks']=array('Q',original)
try:checker.check(0,2,{0:0,1:1},Counter(),{})
except ValueError:pass
else:raise AssertionError('Replaced snapshot accepted')
rc.fields['dest_ranks']=original
assert checker.check(0,2,{0:0,1:1},Counter(),{})==1

assert len(rejected)==4 and all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,rejected=rejected,persistent_buffer_reuse_cycles=20,graph_replacement_rejected=True,scope='Synthetic exact potential inequalities and tamper rejection; not path optimality or native STA.'),indent=2)+'\n')
print('PASS5 exact range cases,4 corrupt certificates,capacity/parent filtering')
