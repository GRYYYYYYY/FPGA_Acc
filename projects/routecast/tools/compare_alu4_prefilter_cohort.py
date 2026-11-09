"""Audit semantic equality and measured wall times for the full cohort pair."""
import hashlib
import json
from pathlib import Path

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

old=Path('experiments/alu4_free_pin_cohort_2026-10-05')
new=Path('experiments/alu4_free_pin_prefilter_cohort_2026-10-05')
a=json.loads((old/'receipt.json').read_text())
b=json.loads((new/'receipt.json').read_text())
eq=json.loads((new/'equivalence.json').read_text())
assert eq['all_final_prediction_fields_exact'] and eq['all_report_decisions_exact']
assert a['input_sha256']==b['input_sha256']
for path,digest in b['input_sha256'].items():
    assert sha(path)==digest,path
assert a['prediction_sha256']==b['prediction_sha256']==sha(new/'prediction.json')==sha(old/'prediction.json')
x=json.loads((old/'query_candidates.json').read_text())
y=json.loads((new/'query_candidates.json').read_text())
assert len(x)==len(y)==len(a['reports'])==len(b['reports'])==1012
pruned=0;found=0
for original,filtered in zip(x,y):
    assert original['cid']==filtered['cid']
    assert original['selection_complete']==filtered['selection_complete']
    assert len(original['targets'])==len(filtered['targets'])
    screening=filtered['delay_prefilter']
    expected=[]
    for before,after in zip(original['targets'],filtered['targets']):
        for field in ('status','path','cost','delay','selected_ipin_ptc','budget','max_labels'):
            assert before[field]==after[field],(original['cid'],field)
        if after['status']=='FOUND':
            found+=1;expected.append(after['selected_ipin_ptc'])
        elif after.get('infeasibility_method')=='shared_exact_delay_prefilter':
            assert after['status']=='UNREACHABLE';pruned+=1
    assert sorted(expected)==screening['feasible_targets']
fields=('cid','net','status','cost','delay','selected_ipin_ptc','committed','before_scores','candidate_scores','selection_complete','optimal_over_supplied_free_targets')
for before,after in zip(a['reports'],b['reports']):
    for field in fields:
        assert before.get(field)==after.get(field),(after['cid'],field)
assert a['final_scores']==b['final_scores']
result={'requests':1012,'found_targets':found,'pruned_targets':pruned,
        'all_target_semantic_results_exact':True,'all_commit_decisions_and_scores_exact':True,
        'prediction_sha256':sha(new/'prediction.json'),
        'baseline_full_wall_s':a['full_wall_s'],'candidate_full_wall_s':b['full_wall_s'],
        'observed_full_wall_ratio':a['full_wall_s']/b['full_wall_s'],
        'baseline_budget_query_s':a['stage_seconds']['budget_query'],
        'candidate_budget_query_s':b['stage_seconds']['budget_query'],
        'source_sha256':sha(__file__),
        'receipt_sha256':{'baseline':sha(old/'receipt.json'),'candidate':sha(new/'receipt.json')},
        'scope':'One historical vs one fresh run on developed alu4; includes driver preparation, query and commit work, excludes upstream pipeline and native feedback. No paired repetitions, native-baseline speedup, unseen-family or hardware claim.'}
(new/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
