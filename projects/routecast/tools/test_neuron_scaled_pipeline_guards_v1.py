"""Controller safety contract: no job launch, real pending gate read-only."""
import json
from pathlib import Path
from run_neuron_scaled_present_pipeline_v1 import stage_action, memory_admission, readiness, R


def main():
    cases=[(None,False,'launch'),(None,True,'unresolved_started_stage'),({'exit_status':0},True,'done'),({'exit_status':1},True,'failed'),({'exit_status':-9},True,'failed'),({},True,'failed'),({'exit_status':False},True,'failed')]
    for terminal,started,expected in cases:assert stage_action(terminal,started)==expected
    g=2**30
    for limit in (8*g,20*g):
        assert memory_admission(limit,80*g-limit-8*g,80*g)['admitted']
        assert not memory_admission(limit,80*g-limit-8*g+1,80*g)['admitted']
    for args in [(-1,0,1),(1,2,1),(True,0,1)]:
        try:memory_admission(*args)
        except ValueError:pass
        else:raise AssertionError('invalid admission accepted')
    f1=readiness(1);f2=readiness(2);f4=readiness(4)
    assert any('factor1_pipeline' in p for p in f2['required'])
    assert any('factor1_pipeline' in p for p in f4['required']) and any('factor2_pipeline' in p for p in f4['required'])
    assert not (R/'experiments/titan23_neuron_scaled_present_factor1_pipeline_v1_2026-10-15').exists()
    from source_binding_v2 import closure
    result=dict(bindings=closure([Path(__file__)]),all_pass=True,stage_state_cases=len(cases),exact_memory_boundary_cases=4,invalid_memory_cases=3,serial_factor_dependencies_pass=True,real_readiness=f1,any_model_or_audit_launched=False,scope='Controller guards only. No full-neuron ablation or performance proof.')
    out=R/'experiments/neuron_scaled_pipeline_guard_contract_v1_2026-10-15';out.mkdir();(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','real_readiness')},indent=2))


if __name__=='__main__':main()
