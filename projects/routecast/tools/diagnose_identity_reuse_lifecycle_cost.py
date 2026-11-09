"""Authenticated cost partition and optimistic arithmetic, not an ablation."""
import json
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'experiments/gf2_identity_reuse_continuous_two_updates_v2_2026-10-06'
cold=ROOT/'experiments/gf2_certified_cold_two_updates_2026-10-06'
for p in (base,cold):
    assert json.loads((p/'verification.json').read_text())['receipt_sha256']==sha(p/'receipt.json')
rows=[]
reference=json.loads((cold/'receipt.json').read_text())['rows']
for row in json.loads((base/'receipt.json').read_text())['rows']:
    w=row['width'];groups=defaultdict(float)
    assert row['complete'] and row['error'] is None
    groups['identity_seed']=row['identity_seed_s'];groups['context_import']=row['context_import_s']
    for rd in row['rounds']:
        groups['prediction']+=rd['stage_s'];groups['prepare_advance']+=rd['prepare_advance_s']
        for stage in rd['stages']:
            name=stage['tool'];log=base/f"gf2_d{w}_round{rd['round']}_{name}.log"
            assert stage['exit_code']==0 and sha(log)==stage['log_sha256']
            if name.startswith('verify_') or name=='audit_candidate.py':key='independent_audits'
            elif 'reference_canonical_reload' in name:key='reference_canonical_analysis'
            elif 'canonical_reload' in name:key='candidate_canonical_analysis'
            elif 'native_import' in name:key='candidate_import_analysis_and_serialization'
            elif 'cold' in name:key='reference_cold_route'
            else:raise ValueError(name)
            groups[key]+=stage['wall_s']
    residual=row['case_wall_s']-sum(groups.values());assert residual>=0
    ref=next(r for r in reference if r['width']==w)['case_wall_s']
    # Deliberately overoptimistic: delete entire import (including analysis),
    # seed and prediction, while retaining every other observed phase.
    impossible=row['case_wall_s']-sum(groups[k] for k in ('identity_seed','prediction','candidate_import_analysis_and_serialization'))
    rows.append(dict(width=w,groups_s=dict(groups),residual_s=residual,wall_s=row['case_wall_s'],cold_wall_s=ref,
                     zero_seed_prediction_and_entire_candidate_import_hypothetical_s=impossible,
                     hypothetical_over_cold=impossible/ref))
out=ROOT/'experiments/gf2_identity_reuse_cost_diagnosis_2026-10-06';out.mkdir()
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings={str(p/'receipt.json'):sha(p/'receipt.json') for p in (base,cold)},rows=rows,scope='Archived wall-time partitions. Entire import includes required native analysis, not removable identity work. Zero phases arithmetic is not an executable policy, causal ablation or statistical benchmark; cold quality policy differs.'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
