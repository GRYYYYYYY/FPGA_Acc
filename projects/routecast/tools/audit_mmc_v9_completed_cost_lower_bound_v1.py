"""Archive a completed sequential stage prefix; no final seed/QoR authentication."""
import json, math
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/ultraembedded_mmc_continuous_workflow_v9_2026-10-09'
stages_bytes=(D/'stages.json').read_bytes();rows_bytes=(D/'rows.json').read_bytes()
stages=json.loads(stages_bytes);rows=json.loads(rows_bytes)
cold=next(row for row in rows if row['arm']=='cold')
assert cold['status']=='COMPLETE_VERIFIED' and cold['continuous_arm_seconds']>0
seed=[s for s in stages if 'log' in s and Path(s['log']).relative_to(D).parts[0]=='seed'][:5]
assert [Path(s['log']).name for s in seed]==['export.log','mmc_rr_audit.log','mmc_scope.log','mmc_scope_audit.log','mmc_model_native_seed.log']
assert all(s['exit_code']==0 and math.isfinite(s['seconds']) and s['seconds']>0 for s in seed)
bound=sum(s['seconds'] for s in seed)
assert bound>cold['continuous_arm_seconds']
handoff=D/'seed/handoff/mmc/receipt.json';data=json.loads(handoff.read_text())
for section in ['bindings','files']:
    assert all(sha(p)==h for p,h in data[section].items())
assert data['required_connections']==data['selected_connections']+data['pending_connections']==115572
outdir=R/'experiments/mmc_v9_completed_cost_lower_bound_v1_2026-10-09';outdir.mkdir()
(outdir/'stages_snapshot.json').write_bytes(stages_bytes)
(outdir/'rows_snapshot.json').write_bytes(rows_bytes)
paths=[Path(__file__),R/'tools/trial_ultraembedded_mmc_continuous_workflow_v9.py',handoff,
       outdir/'stages_snapshot.json',outdir/'rows_snapshot.json',*[Path(s['log']) for s in seed]]
bindings={str(p):sha(p) for p in paths}
out=dict(bindings=bindings,completed_seed_stage_prefix=seed,
         completed_seed_cost_lower_bound_seconds=bound,
         cold_complete_seconds=cold['continuous_arm_seconds'],
         lower_bound_excess_seconds=bound-cold['continuous_arm_seconds'],
         recorded_completed_prefix_already_exceeds_cold=True,
         scope='Completed disjoint sequential producer stages are a lower bound on its full seed arm clock. '
               'Mutable stage/row files archived as snapshots; no skipping remaining work. '
               'Cold COMPLETE_VERIFIED is producer status, not final both-arm authentication. '
               'Remaining independent audits, native quality/canonical admission and final cost remain open. '
               'No independent clock reconstruction, reproducible or causal speedup claim.')
assert all(sha(p)==h for p,h in bindings.items())
(outdir/'audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['bindings','completed_seed_stage_prefix']},indent=2))
