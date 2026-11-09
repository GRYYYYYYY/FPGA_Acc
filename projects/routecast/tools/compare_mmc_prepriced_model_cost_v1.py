"""Authenticated historical model comparison; no full-workflow or causal claim."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R = Path(__file__).resolve().parents[1]
old = R / 'experiments/mmc_resident_hybrid_stats_v6_2026-10-09/mmc'
new = R / 'experiments/mmc_resident_prepriced_stats_v7_2026-10-09/mmc'
bindings = {str(Path(__file__)): sha(Path(__file__))}

def authenticate(path):
    data = json.loads(path.read_text())
    for section in ['bindings', 'files']:
        assert all(sha(p) == h for p, h in data.get(section, {}).items())
    bindings[str(path)] = sha(path)
    return data

parity = authenticate(new / 'semantic_parity_verification.json')
assert parity['complete_outputs_and_all_event_semantics_equal']
assert parity['all_search_dispatch_and_reported_counts_equal']
rows = []
fields = ['total_paid_resident_seconds', 'model_setup_seconds', 'initial_seconds',
          'feedback_seconds', 'cpp_search_seconds', 'cpp_prepare_seconds', 'ledger_check_seconds']
for name, directory in [('original', old), ('prepriced', new)]:
    receipt = authenticate(directory / 'receipt.json')
    branch = authenticate(directory / 'branch_work_verification.json')
    assert branch['all_search_records_match_full_original_NET_phase_and_dispatch']
    assert len(receipt['rounds']) == 2
    rows.append(dict(name=name, receipt_diagnostic_seconds={k: receipt[k] for k in fields},
                     phase_branch_summary=branch['summary']))

phase_differences = {}
assert rows[0]['phase_branch_summary'].keys() == rows[1]['phase_branch_summary'].keys()
for phase, a in rows[0]['phase_branch_summary'].items():
    b = rows[1]['phase_branch_summary'][phase]
    for field in ['queries', 'counts_missing', 'reported_scanned_arcs', 'reported_settled_nodes']:
        assert a[field] == b[field]
    phase_differences[phase] = b['seconds'] - a['seconds']

stages_path = new.parent / 'execution_stages.json'
stages = json.loads(stages_path.read_text())
assert len(stages) == 6 and all(row['exit_code'] == 0 for row in stages)
assert stages[0]['command'][0] == 'tools/run_resident_soft_demand_prepriced_stats_v7.py'
bindings[str(stages_path)] = sha(stages_path)
assert all(sha(p) == h for p, h in bindings.items())
out = dict(bindings=bindings, rows=rows,
           identical_complete_model_semantics_and_reported_work=True,
           observed_phase_branch_seconds_differences=phase_differences,
           observed_receipt_diagnostic_seconds_differences={
               k: rows[1]['receipt_diagnostic_seconds'][k] - rows[0]['receipt_diagnostic_seconds'][k]
               for k in fields},
           candidate_external_model_subprocess_seconds=stages[0]['seconds'],
           scope='Two historical single instrumented development-case model runs, not paired replicates. '
                 'Receipt timing fields sampled at matching producer sites, nested and not additive; '
                 'total_paid_resident_seconds excludes later output hashing/closure. '
                 'Candidate external subprocess time reported separately and not compared to original receipt time. '
                 'Preparation includes price-cache construction. Full conversion/validation/native routing workflow '
                 'and final native quality are not measured here. No causal, stable speedup, heldout or silicon claim.')
directory = R / 'experiments/mmc_prepriced_model_cost_comparison_v1_2026-10-09'
directory.mkdir(exist_ok=True)
(directory / 'comparison.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: v for k, v in out.items() if k not in ['bindings', 'rows']}, indent=2))
