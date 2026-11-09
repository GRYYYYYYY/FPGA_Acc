"""Actual full12 skips plus synthetic real launch and inter-command mutation rejection."""
import json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
from strict_budget_batch_workflow_entry_v1 import execute_batch
from certified_budget_execution_gate_v2 import InvalidEvidence
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/strict_budget_batch_workflow_entry_v1_2026-10-08';D.mkdir(exist_ok=False)
B=R/'experiments/branch_budget_admission_census_v1_2026-10-08';cs=json.loads((B/'protocol.json').read_text())['cases']
plans=json.loads((R/'experiments/retained_seed_session_native_cohort_v3_2026-10-08/protocol.json').read_text())['plans']
cases=[]
for c in cs:
 p=next(p for p in plans if (p['width'],p['index'])==(c['width'],c['index']))
 cases.append(dict(admission=B/f'w{c["width"]}_m{c["index"]}_admission.json',endpoints=c['target'],budget=c['budget'],command=p['command'],cwd=R))
with patch('strict_budget_batch_workflow_entry_v1.subprocess.run',side_effect=AssertionError('Infeasible candidate launched')) as launch:
 real=execute_batch(B/'verification.json',cases,D/'actual')
 assert launch.call_count==0 and len(real['rows'])==12
assert not list((D/'actual').glob('candidate_*.log'))
with tempfile.TemporaryDirectory(prefix='routecast-batch-launch-') as tmp:
 t=Path(tmp);ep=t/'ep.json';bp=t/'bp.json';ap=t/'a.json';vp=t/'v.json'
 ep.write_text(json.dumps({'connections':[{'connection_id':0}]}));bp.write_text(json.dumps({'budgets_ns':{},'default_budget_ns':'1'}))
 ap.write_text(json.dumps({'bindings':{str(ep):sha(ep),str(bp):sha(bp)},'rows':[{'connection_id':0,'minimum_seconds':'1/1000000000','budget_ns':'1','relaxed_path_budget_feasible':True}],'admitted':True}))
 vp.write_text(json.dumps({'all_twelve_cases_independent_admission_pass':True,'bindings':{str(ap):sha(ap)}}))
 base=dict(admission=ap,endpoints=ep,budget=bp,cwd=t)
 positive=execute_batch(vp,[dict(base,command=[sys.executable,'-c','print("contract");raise SystemExit(7)'])],t/'positive')
 assert positive['rows'][0]['candidate_exit_code']==7 and positive['rows'][0]['candidate_quality_accepted'] is False
 first=dict(base,command=[sys.executable,'-c','from pathlib import Path; p=Path("bp.json");p.write_text(p.read_text()+" ")'])
 second=dict(base,command=[sys.executable,'-c','raise SystemExit("must not launch")'])
 try:execute_batch(vp,[first,second],t/'changed')
 except InvalidEvidence as e:assert 'before candidate launch' in str(e)
 else:raise AssertionError('Evidence change between candidates accepted')
 assert (t/'changed/candidate_0.log').exists() and not (t/'changed/candidate_1.log').exists()
p=D/'actual/protocol.json';protocol=json.loads(p.read_text());bindings=dict(protocol['preflight']['bindings'])
for f in (p,D/'actual/receipt.json',Path(__file__),R/'tools/strict_budget_batch_workflow_entry_v1.py',R/'tools/certified_budget_batch_gate_v1.py'):bindings[str(f)]=sha(f)
report=dict(bindings=bindings,all12_actual_skips_zero_intercepted_launches=True,actual_entry_seconds=real['entry_seconds'],synthetic_exit7_propagated=True,inter_command_mutation_prevented_second_launch=True,real_feasible_continue_verified=False,scope='Real12 original-budget batch entry skips plus synthetic command-execution contracts. Synthetic authority is not scientific certification. No floor production cost, quality acceptance or routing speedup.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='bindings'})
