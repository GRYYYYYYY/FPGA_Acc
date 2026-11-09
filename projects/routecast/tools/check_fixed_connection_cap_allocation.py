from fractions import Fraction as F
from pathlib import Path
import json
from fixed_connection_cap_allocation import allocate_budget
from pre_route_endpoints import sha
floor={0:F(1,4),1:F(3,2)};before=dict(floor)
value,valid,b,policy,alpha=allocate_budget(floor,{0},None,F(2),{},True,lambda v:max(v.values()))
assert value==F(3,2) and valid and b=={0:F(1),1:F(3,2)} and alpha is None and floor==before
for supported,target,expanded in ((False,F(2),{0}),(True,F(1),{0}),(True,F(2),{1})):
 result=allocate_budget(floor,expanded,None,target,{},supported,lambda v:max(v.values()));assert not result[1] and result[2]=={}
floor={0:F(1,4),1:F(1,4)};target=F(1);r=allocate_budget(floor,{0,1},None,target,{4:{7}},True,lambda v:sum(v.values()));assert r[1] and sum(r[2].values())>target
assert sum((F(1,3),F(1,3)))<=target and sum((F(3,4),F(3,4)))>target
root=Path(__file__).resolve().parents[1];out=root/'experiments/fixed_connection_cap_contract_2026-10-07';out.mkdir(exist_ok=True);(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),helper_sha256=sha(root/'tools/fixed_connection_cap_allocation.py'),scope='Fixed1ns expanded cap, retained reference reporting envelope, unsupported/planning-target/cap rejection, no initial certified-vector dependency, input nonmutation. Budget envelope may exceed target and actual vectors may pass or fail; complete actual/native gate mandatory, not universal feasibility proof.'),indent=2)+'\n');print('Fixed-cap allocation contract verified',flush=True)
