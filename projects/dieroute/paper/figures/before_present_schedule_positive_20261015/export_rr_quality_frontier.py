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
    ('Ordinary','rr_ordinary_schedule_variant_20261015/three_arm_comparison.json','same_source_ordinary_schedule_three_arms_audited')]:
    proof=read('work/'+path)
    assert proof['status']==status
    for label,result in proof['outcomes'].items():
        add(prefix+': '+label,result['downstream_bounded'])
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
assert all(p['baseline'] or p['cpd_ns']>9.60037 or p['wirelength']>9664 for p in frontier)
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
\begin{axis}[width=14cm,height=8cm,xmin=-4,xmax=15,ymin=-0.4,ymax=8,
xlabel={Wirelength delta from frozen baseline (\%)},
ylabel={CPD delta from frozen baseline (\%)},grid=major,
title={Observed ex5p quality tradeoff: completed five-repeat CPU results},
legend style={at={(0.98,0.98)},anchor=north east,font=\small}]
\fill[green!12] (axis cs:-4,-0.4) rectangle (axis cs:0,0);
\addplot[gray!70,only marks,mark=*,mark size=2pt] coordinates {DOMINATED};
\addlegendentry{Dominated observed variants}
\addplot[red!75!black,only marks,mark=square*,mark size=3pt] coordinates {FRONTIER};
\addlegendentry{Nondominated observed variants}
\addplot[blue!80!black,only marks,mark=star,mark size=4pt] coordinates {(0,0)};
\addlegendentry{Frozen native baseline}
\node[font=\small,anchor=south west] at (axis cs:-2.286837748,6.775051378) {Serial net};
\node[font=\small,anchor=north west] at (axis cs:-1.479718543,6.551101680) {Zero seed};
\end{axis}
\node[align=center,font=\small,anchor=north] at ([yshift=-1.2cm]current axis.south)
{Green: neither WL nor CPD exceeds baseline. No plotted variant enters it.\\
Observed-set frontier only; SLL, board runtime and energy are not represented.};
\end{tikzpicture}
\end{document}
'''
assert {(p['wirelength'],p['cpd_ns']) for p in frontier}=={(9664,9.60037),(9443,10.2508),(9521,10.2293)}
tex=tex.replace('DOMINATED',coordinates([p for p in points if not p['nondominated']]))
tex=tex.replace('FRONTIER',coordinates([p for p in frontier if not p['baseline']]))
(output/'quality_frontier.tex').write_text(tex)
sources['tools/export_rr_quality_frontier.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
manifest=dict(status='observed_completed_native_quality_frontier_exported',rows=rows,unique_points=points,
              frontier=frontier,source_sha256=sources,
              scope='Completed legal five-repeat ex5p variants only, duplicate coordinates grouped. '
                    'Two-metric observed-set dominance, not a global optimum, policy causal comparison, '
                    'SLL acceptance, heldout generalization, physical performance or research completion.',
              board_result=False,research_complete=False)
(output/'quality_frontier_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status=manifest['status'],variants=len(rows),unique_points=len(points),frontier_points=len(frontier))))
