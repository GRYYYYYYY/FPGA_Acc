"""Replay real cohort preflight and reject altered evidence/current inputs."""
import json
import tempfile
import time
from pathlib import Path
from certified_budget_execution_gate_v1 import preflight, InvalidEvidence
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/certified_budget_execution_gate_v1_2026-10-08'
D.mkdir(exist_ok=False)
base=R/'experiments/branch_budget_admission_census_v1_2026-10-08'
authority=base/'verification.json'
protocol=json.loads((base/'protocol.json').read_text())
start=time.perf_counter(); rows=[]
for c in protocol['cases']:
    ap=base/f'w{c["width"]}_m{c["index"]}_admission.json'
    result=preflight(ap,authority,c['target'],c['budget'])
    assert result['run_candidate_pipeline'] is False
    assert result['decision']=='SKIP_CERTIFIED_MODEL_INFEASIBLE'
    rows.append(dict(width=c['width'],index=c['index'],**result))
    print(c['width'],c['index'],'certified skip',len(result['blockers']),flush=True)
# Reject copied or altered supplied inputs and unauthenticated admission evidence.
c=protocol['cases'][0]; ap=base/f'w{c["width"]}_m{c["index"]}_admission.json'
rejected=[]
with tempfile.TemporaryDirectory(prefix='routecast-gate-') as tmp:
    tmp=Path(tmp)
    for kind in ('budget','endpoint','admission','authority'):
        original={'budget':Path(c['budget']),'endpoint':Path(c['target']),
                  'admission':ap,'authority':authority}[kind]
        value=json.loads(original.read_text())
        if kind=='budget': value['default_budget_ns']='1000'
        elif kind=='endpoint': value['connections']=value['connections'][:-1]
        elif kind=='admission': value['admitted']=True
        else: value['all_twelve_cases_independent_admission_pass']=False
        changed=tmp/f'{kind}.json';changed.write_text(json.dumps(value))
        args=[ap,authority,c['target'],c['budget']]
        args[{'admission':0,'authority':1,'endpoint':2,'budget':3}[kind]]=changed
        try: preflight(*args)
        except InvalidEvidence: rejected.append(kind)
        else: raise AssertionError('Altered evidence accepted: '+kind)
assert len(rows)==12 and len(rejected)==4
report=dict(rows=rows,altered_inputs_rejected=rejected,
            verifier_seconds=time.perf_counter()-start,
            source_bindings={str(p):sha(p) for p in
                (Path(__file__),R/'tools/certified_budget_execution_gate_v1.py',authority)},
            production_pipeline_executed=False,
            scope='Real 12-case verified-cache preflight replay, not a fresh floor proof '
                  'or performance experiment. Positive continue branch not exercised '
                  'by this cohort; all 12 original budgets model-infeasible.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: 12 certified skips; 4 altered input/evidence rejections')
