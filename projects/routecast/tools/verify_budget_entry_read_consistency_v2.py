"""Controlled evidence race and subprocess contract; synthetic positive is not scientific admission."""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from certified_budget_execution_gate_v2 import preflight, InvalidEvidence
from strict_budget_workflow_entry_v2 import execute
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/budget_entry_read_consistency_v2_2026-10-08'
D.mkdir(exist_ok=False)
base=R/'experiments/branch_budget_admission_census_v1_2026-10-08'
c=next(c for c in json.loads((base/'protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
real=preflight(base/'w32_m2_admission.json',base/'verification.json',c['target'],c['budget'])
assert real['run_candidate_pipeline'] is False
assert {b['connection_id'] for b in real['blockers']}=={785,1637}
with tempfile.TemporaryDirectory(prefix='routecast-gate-contract-') as tmp:
    t=Path(tmp)
    ep=t/'endpoint.json';bp=t/'budget.json';ap=t/'admission.json';vp=t/'authority.json'
    ep.write_text(json.dumps({'connections':[{'connection_id':0}]}))
    bp.write_text(json.dumps({'default_budget_ns':'1','budgets_ns':{}}))
    ap.write_text(json.dumps({'bindings':{str(ep):sha(ep),str(bp):sha(bp)},'rows':[{'connection_id':0,'minimum_seconds':'1/2000000000','budget_ns':'1','relaxed_path_budget_feasible':True}],'admitted':True}))
    vp.write_text(json.dumps({'all_twelve_cases_independent_admission_pass':True,'bindings':{str(ap):sha(ap)}}))
    for code in (0,7):
        result=execute(ap,vp,ep,bp,[sys.executable,'-c',f'print("contract child");raise SystemExit({code})'],R,t/f'exit{code}')
        assert result['candidate_launched'] and result['candidate_exit_code']==code
        assert result['candidate_quality_accepted'] is False
        assert 'contract child' in (t/f'exit{code}'/'candidate.log').read_text()
    original=Path.read_text
    changed=[False]
    def mutate_after_read(path,*args,**kwargs):
        text=original(path,*args,**kwargs)
        if path==bp and not changed[0]:
            changed[0]=True
            bp.write_text(text+' ')
        return text
    with patch.object(Path,'read_text',mutate_after_read):
        try: preflight(ap,vp,ep,bp)
        except InvalidEvidence as e: assert 'changed during evidence read' in str(e)
        else: raise AssertionError('Evidence mutation accepted')
report={'bindings':{**real['bindings'],**{str(R/'tools'/n):sha(R/'tools'/n) for n in ('certified_budget_execution_gate_v2.py','strict_budget_workflow_entry_v2.py','verify_budget_entry_read_consistency_v2.py')}},'actual_original_budget_skip_preserved':True,'controlled_read_mutation_rejected':True,'actual_subprocess_contract_exit_codes':[0,7],'synthetic_positive_only':True,'real_feasible_continue_workflow_verified':False,'scope':'Controlled temporary synthetic evidence tests API contracts only; authority flag is a fixture, not independently certified routing. No original budget edits, QoR acceptance or gain claim.'}
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
