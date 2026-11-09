"""Actual small-design parity plus independent refusal cases and stage-owner checks."""
import ast,copy,json,hashlib
from pathlib import Path
from audit_raw_floor_initial_parity_v1_2026_10_17 import audit,protocol
R=Path(__file__).resolve().parents[1];D=R/'experiments/neuron_raw_floor_trial_guard_v1_2026-10-17';D.mkdir(exist_ok=False)
A=R/'experiments/xtea_raw_floor_proxy_budget_fixture_v1_2026-10-17/model';B=R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17/model'
load=lambda p:json.loads(p.read_text());a,b=load(A/'initial.json'),load(B/'initial.json');assert audit(a,b)['changed_equal_cost_initial_paths']==383
pa,pb=load(A/'protocol.json'),load(B/'protocol.json');assert protocol(pa,pb)
small={'records':copy.deepcopy(b['records'][:2])};refused=[]
def refuse(name,fn):
 try:fn()
 except (AssertionError,KeyError,TypeError,ValueError):refused.append(name)
 else:raise AssertionError('corruption accepted: '+name)
for key in ['net_id','source','sink','floor_integer','budget_integer']:
 bad=copy.deepcopy(small);bad['records'][0][key]+=1;refuse('record_'+key,lambda bad=bad:audit(bad,small))
for key in ['delay','status']:
 bad=copy.deepcopy(small);bad['records'][0]['answer'][key]=0 if key=='delay' else 'FAILED';refuse('answer_'+key,lambda bad=bad:audit(bad,small))
bad=copy.deepcopy(small);bad['records'].append(copy.deepcopy(bad['records'][0]));refuse('duplicate_CID',lambda:audit(bad,small))
bad=copy.deepcopy(small);bad['records'].pop();refuse('missing_CID',lambda:audit(bad,small))
bad=copy.deepcopy(small);bad['records'][0]['connection_id']=False;refuse('boolean_CID',lambda:audit(bad,small))
for key,value in [('present_factor',2),('rounds',3),('budget_policy','other'),('initial_floor_policy','other'),('new_unregistered_key',1)]:
 bad=copy.deepcopy(pa);bad[key]=value;refuse('protocol_'+key,lambda bad=bad:protocol(bad,pb))
old=R/'tools/neuron_proxy_budget_trial_v2.py';new=R/'tools/neuron_raw_floor_trial_v1_2026_10_17.py'
def fn(path,name):return next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
assert ast.dump(fn(old,'run_stage'),include_attributes=False)==ast.dump(fn(new,'run_stage'),include_attributes=False)
assert ast.dump(fn(old,'baseline_gate'),include_attributes=False)==ast.dump(fn(new,'baseline_gate'),include_attributes=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
files=[Path(__file__).resolve(),old,new,R/'tools/audit_raw_floor_initial_parity_v1_2026_10_17.py',A/'initial.json',B/'initial.json',A/'protocol.json',B/'protocol.json']
with (D/'verification.json').open('x') as f:json.dump(dict(bindings={str(p):sha(p) for p in files},all_pass=True,actual2450_initial_nonpath_records_and_declared_protocol_delta_pass=True,actual_changed_paths=383,negative_cases=refused,negative_cases_count=len(refused),original_run_stage_AST_identical=True,original_baseline_gate_AST_identical=True,scope='Guard/preparation correctness only. Physical path and changed ledger correctness require independent full original auditors; no model or chain submitted by this tool.'),f,indent=2);f.write('\n')
print('PASS actual2450record/protocol guard,',len(refused),'corruptions refused; original stage ownership/resources unchanged')
