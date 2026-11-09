"""Valid query identities, valid individual budgets, incompatible shared parents."""
import json,copy
from pathlib import Path
from criticality_net_admission_v1 import prepare
from pre_route_endpoints import sha
f=dict(row_offsets=[0,2,3,4,4],dest_ranks=[1,2,2,3],edge_ids=[10,11,12,13],capacities=[1]*4);slots={e:i for i,e in enumerate(f['edge_ids'])}
class RC:
 def initial(self,u):return 0
 def increment(self,s):return 1
qs=[dict(connection_id=i,net_id=5,source=0,sink=s) for i,s in enumerate([2,3])]
old=[dict(q,budget_integer=10,answer=dict(status='FOUND',physical_edge_ids=[11] if q['sink']==2 else [11,13],delay=1 if q['sink']==2 else 2)) for q in qs]
new=copy.deepcopy(old);new[1]['answer'].update(physical_edge_ids=[10,12,13],delay=3)
ledger={0:1,2:1,3:1};before=copy.deepcopy((old,new,ledger))
try:prepare(f,RC(),slots,qs,old,new,ledger)
except ValueError as e:assert str(e)=='multiple parents'
else:raise AssertionError('two parents for node2 admitted')
assert (old,new,ledger)==before
# Both paths reparent node2 together: compatible single tree, valid ownership.
new[0]['answer'].update(physical_edge_ids=[10,12],delay=2)
r=prepare(f,RC(),slots,qs,old,new,ledger);assert r['status']=='ADMIT_OCCUPANCY_REPLACEMENT' and r['updates']=={1:1}
out=Path('experiments/criticality_net_parent_conflict_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve()]+[Path('tools')/x for x in ['criticality_net_admission_v1.py','criticality_net_occupancy_gate_v1.py']]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p.resolve()):sha(p) for p in files},identity_consistent_budget_feasible_parent_conflict_rejected=True,joint_reparent_admitted=True,no_rejection_mutation=True),indent=2)+'\n');print('TRUE SHARED PARENT CONFLICT PASS')
