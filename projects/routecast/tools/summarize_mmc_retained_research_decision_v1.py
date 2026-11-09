"""Interpret certified retained-tree metrics against the frozen single-factor control."""
import json
import sys
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure

def main():
    run=R/'experiments/mmc_retained_tree_full_schedule_recovery_v1_2026-10-13'
    metrics_path=R/'experiments/mmc_retained_tree_recovery_hotspots_v1_2026-10-13/verification.json'
    work_path=run/'recorded_work_summary_v1.json'
    metrics=json.loads(metrics_path.read_text());work=json.loads(work_path.read_text())
    bindings=closure([Path(__file__)])
    for p,v in [(metrics_path,metrics),(work_path,work)]:
        assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
    for p in [run/'pipeline_terminal.json',run/'postprocess_terminal.json',run/'model/receipt.json']:
        bindings[str(p)]=sha(p)
    assert json.loads((run/'postprocess_terminal.json').read_text())['all_postprocessing_completed']
    delayed=R/'experiments/mmc_delayed_history_ablation_v1_2026-10-13/model/receipt.json'
    control=json.loads(delayed.read_text());assert all(sha(p)==h for p,h in control['bindings'].items())
    bindings.update(control['bindings']);bindings[str(delayed)]=sha(delayed)
    candidate=metrics['metrics']['candidate_sketch'];baseline=metrics['metrics']['delayed_history_control_sketch']
    comparison={};direction=dict(spearman=1,precision_at_k=1,mae=-1)
    for scope in ['concrete','spatial']:
        comparison[scope]={k:dict(control=baseline[scope][k],candidate=candidate[scope][k],
            delta=candidate[scope][k]-baseline[scope][k],nonworse=direction[k]*(candidate[scope][k]-baseline[scope][k])>=0) for k in direction}
    rounds=work['rounds'];assert [x['overflow_after'] for x in rounds]==[50024,44798]
    control_overflow=control['rounds'][-1]['overflow_after']
    assert control_overflow==45118
    pareto=all(x['nonworse'] for scope in comparison.values() for x in scope.values())
    assert not pareto
    result=dict(bindings=bindings,all_source_audits_and_frozen_metric_bindings_pass=True,
                complete_channel_universe=metrics['complete_channel_universe'],complete_spatial_universe=metrics['complete_spatial_universe'],
                comparison_against_delayed_history_control=comparison,
                final_overflow=dict(control=control_overflow,candidate=44798,delta=44798-control_overflow),
                recorded_primary_calls=sum(x['recorded_primary_search_calls'] for x in rounds),
                retained_connections_across_rounds=sum(x['retained_connections'] for x in rounds),
                resident_seconds=dict(control=control['total_paid_resident_seconds'],candidate=work['timing']['total_paid_resident_seconds']),
                all_quality_metrics_nonworse=pareto,promoted=False,
                decision='Mixed development result: slightly better concrete rho/MAE and spatial rho, lower concrete top-k precision and worse spatial MAE. Lower overflow does not establish better congestion prediction.',
                paired_runtime_speedup_proven=False,native_qor_comparison_completed=False,end_to_end_gain_proven=False,
                scope='Certified complete MMC exposed development comparison, not a heldout-family result. Historical one-shot timing and recorded API counts only; parameters/label scope unchanged.')
    assert all(sha(p)==h for p,h in bindings.items())
    out=R/'experiments/mmc_retained_tree_recovery_decision_v1_2026-10-13';out.mkdir(exist_ok=False)
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2),flush=True)

if __name__=='__main__':main()
