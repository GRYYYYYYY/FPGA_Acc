import copy,json
from pathlib import Path
from criticality_net_admission_v1 import prepare
from pre_route_endpoints import sha
f=dict(row_offsets=[0,3,5,5,5],dest_ranks=[1,2,3,2,3],edge_ids=[10,11,12,13,14],capacities=[1]*4);slots={e:i for i,e in enumerate(f['edge_ids'])};inc=[1,4,4,1,1]
class RC:
 def initial(self,u):return 0
 def increment(self,s):return inc[s]
qs=[dict(connection_id=i,net_id=8,source=0,sink=s) for i,s in enumerate([2,3])]
old=[dict(q,budget_integer=8,floor_integer=2,answer=dict(status='FOUND',physical_edge_ids=[11 if q['sink']==2 else 12],delay=4)) for q in qs]
new=copy.deepcopy(old)
for r in new:r['answer'].update(physical_edge_ids=[10,13 if r['sink']==2 else 14],delay=2)
ledger={0:1,2:1,3:1};frozen=copy.deepcopy((old,new,ledger));r=prepare(f,RC(),slots,qs,old,new,ledger)
assert r['status']=='ADMIT_OCCUPANCY_REPLACEMENT' and r['updates']=={1:1} and (old,new,ledger)==frozen
# Other owner at new branch causes whole-NET rejection.
r=prepare(f,RC(),slots,qs,old,new,{0:1,1:1,2:1,3:1});assert r['status']=='RETAIN_OVERFLOW_INCREASE' and not r['updates']
badcases=[]
a=copy.deepcopy(new);a[0]['budget_integer']=9;badcases.append(a)
a=copy.deepcopy(new);a[0]['answer']['delay']=3;badcases.append(a)
a=copy.deepcopy(new);a[0]['answer']['physical_edge_ids']=[12];badcases.append(a)
a=copy.deepcopy(new);a[0]['net_id']=7;badcases.append(a)
badcases.append(new[:1])
# Parent conflict at shared node2: direct 0->2 versus 0->1->2.
a=copy.deepcopy(new);a[0]['answer'].update(physical_edge_ids=[11],delay=4);a[1]['sink']=2;badcases.append(a)
for a in badcases:
 before=copy.deepcopy((a,ledger))
 try:prepare(f,RC(),slots,qs,old,a,ledger)
 except ValueError:pass
 else:raise AssertionError('invalid tree/metadata admitted')
 assert (a,ledger)==before
out=Path('experiments/criticality_net_admission_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve()]+[Path('tools')/x for x in ['criticality_net_admission_v1.py','criticality_net_occupancy_gate_v1.py']]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p.resolve()):sha(p) for p in files},budget_identity_raw_endpoint_query_scope_rejections=6,occupancy_admit_and_reject_pass=True,no_input_mutation=True,scope='Concrete CSR boundaries; no random full admission or real feedback validation.'),indent=2)+'\n');print('FULL NET ADMISSION BOUNDARIES PASS')
