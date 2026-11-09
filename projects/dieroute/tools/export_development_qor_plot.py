"""Export a PGFPlots figure from completed, audited ex5p development results."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root/'paper/figures'
out.mkdir(exist_ok=True)
inputs = {}


def read(relative):
    path = root/relative
    inputs[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text())


original = read('experiments/wide_timing_cohort_audit_20261013.json')
original = next(x for x in original['experiments'] if 'native_ex5p_' in x['case'])['modes']['downstream_bounded']
stopped = read('work/rr_upstream_target_stop_variant_20261014/independent_audit.json')['experiments'][0]['modes']['downstream_bounded']
fine = read('work/rr_cost_precision_variant_20261014/independent_audit.json')['experiments'][0]['modes']
local = read('work/rr_local_task_order_variant_20261014/independent_audit.json')['experiments'][0]['modes']['downstream_bounded']
cleanup = read('work/rr_wide_cleanup_variant_20261014/independent_audit.json')['experiments'][0]['modes']['downstream_bounded']
cleanup_control = read('work/rr_wide_cleanup_disabled_control_20261014/cleanup_comparison.json')
assert cleanup_control['status']=='same_source_cleanup_pair_audited'
assert cleanup_control['outcomes']['cleanup']['downstream_bounded']==cleanup
seed_control = read('work/rr_tree_seed_zero_variant_20261014/tree_seed_comparison.json')
assert seed_control['status']=='same_source_tree_seed_weight_pair_audited'
seed_zero = seed_control['outcomes']['zero']['downstream_bounded']
midpoint_control = read('work/rr_tree_seed_midpoint_variant_20261014/tree_seed_midpoint_comparison.json')
assert midpoint_control['status']=='same_source_tree_seed_midpoint_pair_audited'
midpoint = midpoint_control['outcomes']['midpoint']['downstream_bounded']
span_control = read('work/rr_main_span_cost_variant_20261014/span_price_comparison.json')
assert span_control['status']=='same_source_channel_span_price_pair_audited'
span = span_control['outcomes']['priced']['downstream_bounded']
rows = []
for ident,(label,result) in enumerate([('Original downstream',original),('Entry stop',stopped),
                                      ('Fine flat',fine['flat']),('Fine entry',fine['downstream_bounded']),
                                      ('Local first',local),('Cleanup',cleanup),('Zero seed',seed_zero),('Half seed',midpoint),('Span price',span)]):
    assert result['status'] == 'passed' and result['repeats_verified'] == 5 and result['fixed_point_valid']
    q = result['native_qor']
    assert q['baseline_wirelength'] == 9664 and q['baseline_cpd_ns'] == 9.60037
    rows.append(dict(id=ident,label=label,wire_percent=q['wirelength_delta_percent'],
                     cpd_percent=q['cpd_delta_percent'],expansions_m=result['counters']['expanded']/1e6))
with (out/'development_qor.tsv').open('w') as stream:
    stream.write('id wire_percent cpd_percent expansions_m\n')
    for row in rows:
        stream.write(f"{row['id']} {row['wire_percent']:.8f} {row['cpd_percent']:.8f} {row['expansions_m']:.8f}\n")
tex = r'''\documentclass[tikz,border=5pt]{standalone}
\usepackage{pgfplots}
\usepgfplotslibrary{groupplots}
\pgfplotsset{compat=1.18}
\begin{document}
\begin{tikzpicture}
\begin{groupplot}[group style={group size=1 by 3,vertical sep=1.4cm},
width=14cm,height=4.6cm,ybar,/pgf/bar width=17pt,ymin=0,ymajorgrids=true,
xtick={0,1,2,3,4,5,6,7,8},xticklabels={Original\\downstream,Entry\\stop,Fine\\flat,Fine\\entry,Local\\first,Cleanup,Zero\\seed,Half\\seed,Span\\price},
xticklabel style={align=center,font=\footnotesize},enlarge x limits=0.15,
nodes near coords,every node near coord/.append style={font=\scriptsize},
point meta=y]
\nextgroupplot[ymin=-5,ymax=16,ylabel={Wirelength delta (\%)},title={ex5p: five audited deterministic CPU repetitions}]
\addplot[fill=blue!45,draw=blue!70!black] table[x=id,y=wire_percent] {development_qor.tsv};
\nextgroupplot[ymax=8,ylabel={CPD delta (\%)}]
\addplot[fill=orange!55,draw=orange!70!black] table[x=id,y=cpd_percent] {development_qor.tsv};
\nextgroupplot[ymax=70,ylabel={Expanded nodes (millions)}]
\addplot[fill=gray!45,draw=black] table[x=id,y=expansions_m] {development_qor.tsv};
\end{groupplot}
\node[align=center,font=\small,anchor=north] at ([yshift=-1.3cm]group c1r3.south)
{Positive QoR deltas are worse than the frozen native baseline.\\Work counts are not elapsed time, board speedup or energy.};
\end{tikzpicture}
\end{document}
'''
(out/'development_qor.tex').write_text(tex)
inputs['tools/export_development_qor_plot.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(out/'development_qor_manifest.json').write_text(json.dumps(dict(status='audited_plot_data_exported',rows=rows,
    source_sha256=inputs,scope='Nine ex5p development variants; completed evidence only, including matched-source cleanup, seed-weight and span-price controls. Not a general or board comparison',
    research_complete=False,board_result=False),indent=2)+'\n')
print(json.dumps(dict(status='audited_plot_data_exported',variants=len(rows))))
