"""Summarize the observed WL/CPD frontier without changing the research acceptance gate."""
import hashlib
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
output=root/'paper/figures'
sources={}


def read(path):
    file=root/path
    sources[path]=hashlib.sha256(file.read_bytes()).hexdigest()
    return json.loads(file.read_text())


rows=[]


def add(label,result):
    assert result['status']=='passed' and result['repeats_verified']==5 and result['fixed_point_valid']
    assert result['counters']['legal']
    q=result['native_qor']
    assert (q['baseline_wirelength'],q['baseline_cpd_ns'])==(9664,9.60037)
    rows.append(dict(label=label,wirelength=q['total_wirelength'],cpd_ns=q['critical_path_delay_ns']))


cohort=read('experiments/wide_timing_cohort_audit_20261013.json')
add('Original downstream',next(e for e in cohort['experiments'] if 'native_ex5p_' in e['case'])['modes']['downstream_bounded'])
for name,path in [('Entry stop','rr_upstream_target_stop_variant_20261014'),
                  ('Local first','rr_local_task_order_variant_20261014'),
                  ('Cleanup','rr_wide_cleanup_variant_20261014')]:
    add(name,read(f'work/{path}/independent_audit.json')['experiments'][0]['modes']['downstream_bounded'])
fine=read('work/rr_cost_precision_variant_20261014/independent_audit.json')['experiments'][0]['modes']
add('Fine flat',fine['flat'])
add('Fine entry',fine['downstream_bounded'])
for label,path,status,key in [
    ('Zero seed','rr_tree_seed_zero_variant_20261014/tree_seed_comparison.json','same_source_tree_seed_weight_pair_audited','zero'),
    ('Half seed','rr_tree_seed_midpoint_variant_20261014/tree_seed_midpoint_comparison.json','same_source_tree_seed_midpoint_pair_audited','midpoint'),
    ('Span price','rr_main_span_cost_variant_20261014/span_price_comparison.json','same_source_channel_span_price_pair_audited','priced')]:
    proof=read('work/'+path)
    assert proof['status']==status
    add(label,proof['outcomes'][key]['downstream_bounded'])
for prefix,path,status in [
    ('Feedback','rr_critical_feedback_variant_20261014/feedback_comparison.json','same_source_critical_feedback_pair_audited'),
    ('Local guard','rr_local_delay_feedback_variant_20261014/three_arm_comparison.json','same_source_local_delay_feedback_three_arms_audited'),
    ('Whole net','rr_supplemental_net_transaction_variant_20261015/three_arm_comparison.json','same_source_supplemental_net_trial_three_arms_audited'),
    ('Ordinary','rr_ordinary_schedule_variant_20261015/three_arm_comparison.json','same_source_ordinary_schedule_three_arms_audited'),
    ('Present','rr_present_schedule_variant_20261015/three_arm_comparison_v2.json','same_source_present_schedule_three_arms_audited'),
    ('Retention','rr_legal_connection_retention_variant_20261015/paired_comparison.json','same_source_legal_connection_retention_pair_audited')]:
    proof=read('work/'+path)
    assert proof['status']==status
    for label,result in proof['outcomes'].items():
        add(prefix+': '+label,result['downstream_bounded'])
criticality=read('work/rr_criticality_shift_variant_20261015/result.json')
assert criticality['status']=='ten_run_criticality_transform_pair_native_and_independent_state_audits_complete'
for mode,label in enumerate(['clamp','shift']):
    result=criticality['outcomes'][label]
    assert result['counters']['legal']
    for repeat in range(5):
        audit=read(f'work/rr_criticality_shift_variant_20261015/native_runs_v2/mode{mode}_{repeat}/transformed_resource_replay_audit.json')
        assert audit['result']['criticality_transform_mode']==mode and audit['result']['final_resources_and_costs_byte_equivalent']
    q=result['native_qor']
    assert (q['baseline_wirelength'],q['baseline_cpd_ns'])==(9664,9.60037)
    rows.append(dict(label='Criticality: '+label,wirelength=q['total_wirelength'],cpd_ns=q['critical_path_delay_ns']))
initial=read('work/rr_native_initial_criticality_study_20261015/result.json')
assert initial['status']=='ten_initial_criticality_runs_native_validations_and_independent_audits_complete'
for label in ['uniform','native']:
    result=initial['outcomes'][label]
    assert result['counters']['legal']
    for repeat in range(5):
        audit=read(f'work/rr_native_initial_criticality_study_20261015/runs/{label}_{repeat}/resource_replay_audit.json')
        assert audit['result']['final_resources_and_costs_byte_equivalent'] and audit['result']['cpu_legal']
    q=result['native_qor']
    assert (q['baseline_wirelength'],q['baseline_cpd_ns'])==(9664,9.60037)
    rows.append(dict(label='Initial: '+label,wirelength=q['total_wirelength'],cpd_ns=q['critical_path_delay_ns']))
fanout=read('work/rr_fanout_net_order_variant_20261015/native_result.json')
fanout_review=read('work/rr_fanout_net_order_variant_20261015/terminal_evidence_review.json')
assert fanout['status']=='twenty_native_fanout_schedule_runs_and_independent_audits_complete'
assert fanout_review['result_sha256']==sources['work/rr_fanout_net_order_variant_20261015/native_result.json']
for arm,result in fanout['outcomes'].items():
    for repeat in range(5):
        audit=read(f'work/rr_fanout_net_order_variant_20261015/native_runs/{arm}_{repeat}/dispatch_resource_replay_audit.json')
        assert audit['cpu_legal'] and audit['final_resources_and_costs_byte_equivalent']
    q=result['native_qor']
    assert q['legal'] and (q['baseline_wirelength'],q['baseline_cpd_ns'])==(9664,9.60037)
    rows.append(dict(label='Fanout factorial: '+arm,wirelength=q['total_wirelength'],cpd_ns=q['critical_path_delay_ns']))
seed_weight=read('work/rr_fanout_seed_weight_variant_v3_20261015/independent_audit.json')
assert seed_weight['status']=='ten_native_seed_weight_runs_reviewed_joint_quality_failed'
for arm,result in seed_weight['outcomes'].items():
    assert result['repeats']==5 and not result['joint_quality_pass']
    rows.append(dict(label='Fanout serial seed: '+arm,wirelength=result['wirelength'],cpd_ns=result['cpd_ns']))
fanout_present=read('work/rr_fanout_present_interaction_variant_v2_20261015/independent_audit.json')
assert fanout_present['status']=='twenty_native_fanout_present_runs_independently_reviewed'
for arm,result in fanout_present['outcomes'].items():
    assert result['repeats']==5 and result['checks']['native_legal']
    rows.append(dict(label='Fanout-present: '+arm,wirelength=result['wirelength'],cpd_ns=result['cpd_ns']))
baseline_log=root/'work/native_ex5p_stratix2die_cw80_20261013/vpr.log'
text=baseline_log.read_text()
assert int(re.findall(r'Total wirelength:\s+(\d+)',text)[-1])==9664
assert float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',text)[-1])==9.60037
sources[str(baseline_log.relative_to(root))]=hashlib.sha256(baseline_log.read_bytes()).hexdigest()
groups={}
for row in [dict(label='Frozen baseline',wirelength=9664,cpd_ns=9.60037),*rows]:
    key=(row['wirelength'],row['cpd_ns'])
    groups.setdefault(key,[]).append(row['label'])
points=[]
for (wl,cpd),labels in sorted(groups.items()):
    dominators=[dict(wirelength=w,cpd_ns=c,labels=names) for (w,c),names in groups.items()
                if w<=wl and c<=cpd and (w<wl or c<cpd)]
    points.append(dict(wirelength=wl,cpd_ns=cpd,labels=labels,dominated_by=dominators,
                       nondominated=not dominators,baseline=(wl,cpd)==(9664,9.60037),
                       wire_percent=(wl/9664-1)*100,cpd_percent=(cpd/9.60037-1)*100))
frontier=[p for p in points if p['nondominated']]
improving=[p for p in points if not p['baseline'] and p['cpd_ns']<=9.60037 and p['wirelength']<=9664]
assert len(improving)==1 and improving[0]['wirelength']==9512 and improving[0]['cpd_ns']==9.54931
with (output/'quality_frontier.tsv').open('w') as stream:
    stream.write('id wire_percent cpd_percent nondominated baseline\n')
    for i,p in enumerate(points):
        stream.write(f"{i} {p['wire_percent']:.9f} {p['cpd_percent']:.9f} {int(p['nondominated'])} {int(p['baseline'])}\n")


def coordinates(selected):
    return ' '.join(f"({p['wire_percent']:.9f},{p['cpd_percent']:.9f})" for p in selected)


tex=r'''\documentclass[tikz,border=5pt]{standalone}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\begin{document}
\begin{tikzpicture}
\begin{axis}[width=14cm,height=8cm,xmin=-4,xmax=15,ymin=-1,ymax=8,
xlabel={Wirelength delta from frozen baseline (\%)},
ylabel={CPD delta from frozen baseline (\%)},grid=major,
title={Observed ex5p quality tradeoff: completed five-repeat CPU results},
legend style={at={(0.98,0.98)},anchor=north east,font=\small}]
\fill[green!12] (axis cs:-4,-1) rectangle (axis cs:0,0);
\addplot[gray!70,only marks,mark=*,mark size=2pt] coordinates {DOMINATED};
\addlegendentry{Dominated observed variants}
\addplot[red!75!black,only marks,mark=square*,mark size=3pt] coordinates {FRONTIER};
\addlegendentry{Nondominated observed variants}
\addplot[blue!80!black,only marks,mark=star,mark size=4pt] coordinates {(0,0)};
\addlegendentry{Frozen native baseline}
\node[font=\small,anchor=south west] at (axis cs:-2.524834437,1.525357876) {Fanout serial};
\draw[gray!60] (axis cs:-1.572847682,-0.531854501) -- (axis cs:0.5,-0.531854501);
\node[font=\small,anchor=west] at (axis cs:0.6,-0.531854501) {Zero first epoch};
\end{axis}
\node[align=center,font=\small,anchor=north] at ([yshift=-1.2cm]current axis.south)
{Green: neither WL nor CPD exceeds baseline. One plotted variant enters it.\\
Observed-set frontier only; SLL, board runtime and energy are not represented.};
\end{tikzpicture}
\end{document}
'''
assert {(p['wirelength'],p['cpd_ns']) for p in frontier}=={(9420,9.74681),(9512,9.54931)}
tex=tex.replace('DOMINATED',coordinates([p for p in points if not p['nondominated'] and not p['baseline']]))
tex=tex.replace('FRONTIER',coordinates([p for p in frontier if not p['baseline']]))
(output/'quality_frontier.tex').write_text(tex)
sources['tools/export_rr_quality_frontier.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
manifest=dict(status='observed_completed_native_quality_frontier_exported',rows=rows,unique_points=points,
              frontier=frontier,two_metric_non_degrading_variants=improving,source_sha256=sources,
              scope='Completed legal five-repeat ex5p variants only, duplicate coordinates grouped. '
                    'Two-metric observed-set dominance, not a global optimum, policy causal comparison, '
                    'SLL acceptance, heldout generalization, physical performance or research completion.',
              board_result=False,research_complete=False)
(output/'quality_frontier_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status=manifest['status'],variants=len(rows),unique_points=len(points),frontier_points=len(frontier))))
