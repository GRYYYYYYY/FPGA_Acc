"""Plot three completed, independently audited CPU configurations separately."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [ROOT / 'work/upstream_hash_five_pair_summary_20261018/audit.json',
           ROOT / 'work/upstream_hash_crosscase_pairs_20261018/independent_case_audit_diffeq.json',
           ROOT / 'work/upstream_hash_crosscase_pairs_20261018/independent_case_audit_alu4.json']

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    if args.check_only:
        print(json.dumps({'all_three_completed_audits_available': all(p.is_file() for p in SOURCES),
                          'available': {p.parent.name + '/' + p.name: p.is_file() for p in SOURCES},
                          'render_started': False}))
        return
    assert all(p.is_file() for p in SOURCES), 'All three complete five-pair audits required'
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    cases = []
    for source, name, scale in zip(SOURCES, ['ex5p', 'diffeq', 'alu4'], [1, 256, 256]):
        audit = json.loads(source.read_text())
        for path, expected in audit['source_sha256'].items():
            assert sha(path) == expected, path
        if name == 'ex5p':
            assert audit['status'] == 'all_five_native_CPU_pairs_reviewed_outputs_and_sessions_consistent'
            pairs = audit['pairs']
        else:
            assert audit['status'] == 'one_development_case_all10_outputs_sessions_and_matched_times_reviewed'
            case, = audit['cases']
            assert case['case'] == name and case['cost_scale'] == scale
            pairs = case['pairs']
        assert len(pairs) == 5 and [p['pair'] for p in pairs] == list(range(5))
        rows = []
        for pair in pairs:
            reduction = 100 * (1 - pair['candidate_ns'] / pair['parent_ns'])
            assert math.isclose(reduction, -pair['candidate_change_percent'], abs_tol=1e-10)
            rows.append({'case': name, 'cost_scale': scale, 'pair': pair['pair'] + 1,
                         'parent_seconds': pair['parent_ns'] / 1e9,
                         'candidate_seconds': pair['candidate_ns'] / 1e9,
                         'time_reduction_percent': reduction})
        cases.append({'case': name, 'scale': scale, 'rows': rows,
                      'median_reduction_percent': statistics.median(v['time_reduction_percent'] for v in rows)})
    out = ROOT / 'paper/figures'
    base = out / 'upstream_hash_three_case_pairs'
    rows = [row for case in cases for row in case['rows']]
    with base.with_suffix('.tsv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)
    low = min(0, math.floor(min(row['time_reduction_percent'] for row in rows)))
    high = math.ceil(max(row['time_reduction_percent'] for row in rows)) + 2
    lines = [r'\documentclass[tikz,border=3pt]{standalone}', r'\usepackage{pgfplots}',
             r'\usepgfplotslibrary{groupplots}', r'\pgfplotsset{compat=1.18}',
             r'\begin{document}', r'\begin{tikzpicture}',
             r'\begin{groupplot}[group style={group size=3 by 1,horizontal sep=1cm},width=5cm,height=5.5cm,'
             r'xlabel={Matched pair},xtick={1,2,3,4,5},ymin=' + str(low) + ',ymax=' + str(high) +
             r',enlarge x limits=.15,grid=major,grid style={gray!15},title style={font=\small}]']
    for index, case in enumerate(cases):
        title = case['case'] + ' (scale ' + str(case['scale']) + ')'
        label = r'ylabel={Complete process time reduction (\%)},' if index == 0 else 'yticklabels={},'
        lines.append(r'\nextgroupplot[' + label + 'title={' + title + '}]')
        coords = ' '.join(f"({row['pair']},{row['time_reduction_percent']:.8f})" for row in case['rows'])
        lines.append(r'\addplot[ybar,/pgf/bar width=11pt,fill=blue!60,draw=none] coordinates {' + coords + '};')
        median = case['median_reduction_percent']
        lines.append(r'\addplot[black,dashed,domain=.5:5.5] {' + str(median) + '};')
        lines.append(r'\node[anchor=north,font=\scriptsize] at (rel axis cs:.5,.98) {Median ' + f'{median:.2f}' + r'\%};')
    lines.extend([r'\end{groupplot}', r'\node[anchor=north,font=\scriptsize,align=center,yshift=-30pt] at (group c2r1.south) {Three separate development configurations; five alternating-order pairs each.\\Shared host and warm caches; no pooled estimate or FPGA speedup.};',
                  r'\end{tikzpicture}', r'\end{document}'])
    base.with_suffix('.tex').write_text('\n'.join(lines) + '\n')
    with base.with_suffix('.build.stdout').open('w') as log:
        subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', '-output-directory', str(out), str(base.with_suffix('.tex'))], stdout=log, stderr=subprocess.STDOUT, check=True)
    subprocess.run(['pdftoppm', '-singlefile', '-r', '150', '-png', str(base.with_suffix('.pdf')), str(base)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    report = {'status': 'three_separate_completed_five_pair_CPU_configurations_rendered', 'cases': cases,
              'source_sha256': {str(p): sha(p) for p in [*SOURCES, Path(__file__).resolve()]},
              'artifacts_sha256': {str(base.with_suffix(ext)): sha(base.with_suffix(ext)) for ext in ['.tex', '.tsv', '.pdf', '.png']},
              'scope': 'Separate CPU process-time comparisons; cost scales retained. No pooled statistical estimate, representative guarantee, adoption or physical FPGA result.',
              'research_complete': False}
    base.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(base.with_suffix('.png'))

if __name__ == '__main__':
    main()
