"""Authenticate completed v10 stage observations and check accounting, not clock truth."""
import json, math, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
from pre_route_endpoints import sha
D = R / 'experiments/ultraembedded_mmc_continuous_workflow_v10_2026-10-09'
def load(p): return json.loads(p.read_text())
v = load(D / 'verification.json')
assert v['all_cases_both_complete_arms_authenticated']
for p, h in v['bindings'].items(): assert sha(p) == h
receipt = load(D / 'receipt.json')
assert receipt['files'][str(D / 'stages.json')] == sha(D / 'stages.json')
s = load(D / 'stages.json')
bindings = {str(p): sha(p) for p in [D / 'verification.json', D / 'stages.json', D / 'receipt.json', Path(__file__)]}
arms = {'cold': [], 'seed': []}
for x in s:
    assert math.isfinite(x['seconds']) and x['seconds'] > 0
    if 'log' in x:
        p = Path(x['log']); assert p.is_file() and x['exit_code'] == 0
        arm = p.relative_to(D).parts[0]
        bindings[str(p)] = sha(p)
    else:
        assert x['stage'] in ['seed_selection_and_serialization', 'canonical_reload_complete']
        arm = x.get('arm', 'seed')
    assert arm in arms
    arms[arm].append(x)
assert [len(arms[a]) for a in ['cold', 'seed']] == [8, 10]
def label(x):
    return Path(x['log']).name if 'log' in x else x['stage']
common_start=['export.log','mmc_rr_audit.log','mmc_scope.log','mmc_scope_audit.log']
common_end=['native.log','mmc_native_audit.log','canonical_reload_complete','ignored_audit.log']
assert [label(x) for x in arms['cold']] == common_start+common_end
assert [label(x) for x in arms['seed']] == common_start+['mmc_model_native_seed.log','mmc_shared_audits.log']+common_end

rows = []
for row in load(D / 'receipt.json')['rows']:
    arm = row['arm']; stages = arms[arm]
    total = row['continuous_arm_seconds']; accounted = sum(x['seconds'] for x in stages)
    assert row['status'] == 'COMPLETE_VERIFIED' and 0 < accounted < total
    rows.append(dict(arm=arm, total_seconds=total, recorded_stage_seconds=accounted,
                     unassigned_seconds=total-accounted, stages=stages))
out = dict(bindings=bindings, stage_accounting_pass=True, rows=rows,
           scope='Stage observations authenticated against producer receipt and final scientific verification; exact complete stage order and log completion checked. Arithmetic only, not independent wall-clock reconstruction or reproducibility evidence. Final archival hash excluded from arm timers per protocol.')
assert all(sha(p) == h for p,h in bindings.items())
(D / 'stage_cost_verification_v7.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps([{k: val for k,val in row.items() if k != 'stages'} for row in rows], indent=2))
