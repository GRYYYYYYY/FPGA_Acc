"""Resource execution reuse by exact AST, complete-event admission corruption gates."""
import ast
import copy
import json
from pathlib import Path
import neuron_continue_primary_trial_v1 as trial
import neuron_no_retention_trial_v2 as old


def functions(path):
    return {n.name:n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef)}


def main():
    original=functions(old.__file__)
    text=Path(trial.__file__).read_text().replace('CONTINUE PRIMARY START','RETENTION CAUSAL START').replace('continue-after-rejection','retention-only').replace("'continued1'","'unseeded1'")
    candidate={n.name:n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
    for name in ('baseline_gate','run_stage','run','metrics'):
        assert ast.dump(original[name],include_attributes=False)==ast.dump(candidate[name],include_attributes=False),name
    assert trial.evaluate_frame is old.evaluate_frame
    protocol=trial.load(trial.OUT/'protocol.json');assert protocol['metric_methods']==['retained1','continued1'] and protocol['metric_sets']==8
    assert protocol['concrete_count']==1678392 and protocol['concrete_k']==83920 and protocol['spatial_count']==48194 and protocol['spatial_k']==20
    trial.check(protocol['bindings'])
    # Execute the actual independent-admission event membership checks.
    node=next(n for n in ast.walk(functions(trial.__file__)['admit']) if isinstance(n,ast.If) and ast.unparse(n.test)=="kind == 'event'")
    code=compile(ast.Module(body=node.body[:-1],type_ignores=[]),str(trial.__file__),'exec')
    good=dict(net_id=56,retained_connection_ids=[0],primary_search_connection_ids=[1,2],primary_search_calls=2,primary_rejected_expansions=[dict(connection_id=1)])
    exec(code,dict(item=good,query_cids={56:{0,1,2}}))
    corrupt=[]
    for field,value in [('retained_connection_ids',[0,0]),('primary_search_connection_ids',[1]),('primary_search_connection_ids',[0,1,2]),('primary_search_calls',3),('primary_rejected_expansions',[dict(connection_id=0)])]:
        e=copy.deepcopy(good);e[field]=value;corrupt.append(e)
    for event in corrupt:
        try:exec(code,dict(item=event,query_cids={56:{0,1,2}}))
        except AssertionError:pass
        else:raise AssertionError('Corrupt final-admission membership accepted')
    prior=[trial.R/'experiments/neuron_no_retention_trial_guard_v1_2026-10-17/verification.json',trial.R/'experiments/no_retention_v2_kernel_limit_and_kill_v1_2026-10-17/verification.json']
    for p in prior:
        v=trial.load(p);assert v['all_pass'];trial.check(v['bindings'])
    ready=trial.baseline_gate()
    assert not (trial.OUT/'process.json').exists()
    out=trial.R/'experiments/neuron_continue_primary_trial_guard_v1_2026-10-17';out.mkdir()
    trial.write(out/'verification.json',dict(all_pass=True,bindings={str(p):trial.sha(p) for p in (Path(__file__),Path(trial.__file__),trial.OUT/'protocol.json',*prior)},
        baseline_gate_and_stage_run_and_metrics_AST_identical_except_method_and_log_labels=True,
        existing_real_child_success_failure_timeout_kernel_cap_kill_and_no_retry_evidence_reused=True,
        actual_closed_baseline_ready=ready,full_admission_corruption_cases_refused=len(corrupt),same_exact_all8_metric_function_and_domains=True,new_neuron_model_submitted=False))
    print('PASS original resource/timeout/no-retry execution AST;5 admission corruptions; complete baseline ready')


if __name__=='__main__':main()
