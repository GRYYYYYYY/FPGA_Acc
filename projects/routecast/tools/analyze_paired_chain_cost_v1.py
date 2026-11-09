"""Authenticated retrospective cost decomposition; no new runtime experiment."""
import json
import math
from pathlib import Path
from pre_route_endpoints import sha

R = Path(__file__).resolve().parents[1]
E = R / 'experiments'
D = E / 'paired_chain_cost_decomposition_v1_2026-10-09'
bindings = {str(Path(__file__).resolve()): sha(Path(__file__))}

def read_receipt(path):
    data = json.loads(path.read_text())
    bindings[str(path)] = sha(path)
    for name, digest in data['bindings'].items():
        assert sha(Path(name)) == digest, name
        assert name not in bindings or bindings[name] == digest
        bindings[name] = digest
    return data

full = read_receipt(E / 'paired_optimized_chain_v1_2026-10-09/verification.json')
rows = []
for arm in (0, 3):
    workflow = next(row['workflow_seconds'] for row in full['rows'] if row['arm'] == arm)
    phases = {}
    component = 0.0
    steps = []
    for step in (1, 2, 3):
        receipt = read_receipt(E / f'paired_optimized_chain_v1_arm{arm}_step{step}_v1_2026-10-09/verification.json')
        assert receipt['status'] == 'FOUND_REQUIRES_INDEPENDENT_FULL_GATES'
        total = receipt['component_seconds']
        measured = sum(receipt['phase_seconds'].values())
        assert all(math.isfinite(v) and v >= 0 for v in receipt['phase_seconds'].values())
        assert total >= measured
        component += total
        for name, value in receipt['phase_seconds'].items():
            phases[name] = phases.get(name, 0.0) + value
        steps.append(dict(step=step, component_seconds=total,
                          phase_seconds=receipt['phase_seconds'],
                          phase_calls=receipt['phase_calls'],
                          uninstrumented_component_seconds=total-measured))
    assert workflow >= component
    rows.append(dict(arm=arm, workflow_seconds=workflow, steps=steps,
                     component_seconds=component, phase_seconds=phases,
                     uninstrumented_component_seconds=component-sum(phases.values()),
                     outside_production_components_seconds=workflow-component,
                     solver_share_of_workflow=phases['solver']/workflow))
means = {key: sum(row[key] for row in rows)/2 for key in
         ('workflow_seconds', 'component_seconds', 'outside_production_components_seconds',
          'uninstrumented_component_seconds')}
phase_means = {name: sum(row['phase_seconds'][name] for row in rows)/2
               for name in rows[0]['phase_seconds']}
cold = full['cold_mean_seconds']
# Deliberately optimistic lower bounds: no implementation is claimed.
counterfactuals = {
    'remove_all_solver_time_seconds': means['workflow_seconds']-phase_means['solver'],
    'remove_entire_production_components_seconds': means['outside_production_components_seconds'],
}
report = dict(bindings=bindings, rows=rows, means=means, phase_means=phase_means,
              cold_mean_seconds=cold, optimistic_counterfactuals=counterfactuals,
              counterfactual_to_cold_ratios={k: v/cold for k,v in counterfactuals.items()},
              scope='Retrospective same-run nested timers. Residual includes uninstrumented '
                    'setup/artifact costs; outside-production residual includes subprocess startup, '
                    'independent audits, native/canonical stages, optimization and publication. '
                    'No per-stage attribution of residual, no new benchmark, no achievable speedup claim. '
                    'Budget fixtures are positive controls, not independent timing requirements.')
for name, digest in bindings.items():
    assert sha(Path(name)) == digest
D.mkdir(exist_ok=False)
(D/'report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(dict(means=means, phase_means=phase_means,
                     counterfactuals=counterfactuals, cold_mean_seconds=cold), indent=2))
