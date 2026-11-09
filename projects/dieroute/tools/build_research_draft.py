"""Build the preliminary manuscript after loading the persistent TeX environment."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pdflatex', default='pdflatex')
args = parser.parse_args()
compiler = shutil.which(args.pdflatex)
if not compiler:
    raise SystemExit('Load the persistent texlive/setup.sh environment, then rerun.')
root = Path(__file__).resolve().parents[1]
paper = root / 'paper'
subprocess.run([sys.executable, str(root/'tools/plot_sb_development_quality.py'), '--pdflatex', compiler], cwd=root, check=True)
subprocess.run([sys.executable, str(root/'tools/render_sb_ex5p_native_STA_paths.py'), '--pdflatex', compiler], cwd=root, check=True)
subprocess.run([sys.executable, str(root/'tools/plot_refreshed_native_quality.py')], cwd=root, check=True)
subprocess.run([sys.executable, str(root/'tools/plot_upstream_hash_native_pairs.py')], cwd=root, check=True)
subprocess.run([sys.executable, str(root/'tools/plot_upstream_hash_three_case_pairs.py')], cwd=root, check=True)
subprocess.run([sys.executable, str(root/'tools/plot_width_first_five_quality.py')], cwd=root, check=True)
subprocess.run([sys.executable, str(root/'tools/plot_width_all_twelve_quality.py')], cwd=root, check=True)
(paper/'research_plan_snapshot.json').write_bytes((root/'experiments/research_plan.json').read_bytes())
subprocess.run([sys.executable, str(root/'tools/export_research_draft_evidence.py')], cwd=root, check=True)
command = [compiler, '-interaction=nonstopmode', '-halt-on-error', 'dieroute.tex']
with (paper/'build.log').open('w') as log:
    for _ in range(2):
        subprocess.run(command, cwd=paper, stdout=log, stderr=subprocess.STDOUT, check=True)
text = (paper/'dieroute.log').read_text()
assert not re.search(r'undefined references|Reference .* undefined|Overfull', text)
assert 'Output written' in text and (paper/'dieroute.pdf').stat().st_size > 0
evidence = json.loads((paper/'evidence_manifest.json').read_text())
assert all(hashlib.sha256((root/p).read_bytes()).hexdigest() == h
           for p,h in evidence['source_sha256'].items())
paths = ['paper/dieroute.tex', 'paper/evidence.tex', 'paper/evidence_manifest.json', 'paper/research_plan_snapshot.json',
         'paper/dieroute.pdf', 'paper/build.log', 'tools/build_research_draft.py',
         'tools/export_research_draft_evidence.py', 'paper/related_work_sources.json',
         'paper/figures/quality_frontier.pdf', 'paper/figures/quality_frontier.tex',
         'paper/figures/quality_frontier.tsv', 'paper/figures/quality_frontier_manifest.json',
         'tools/export_rr_quality_frontier.py', 'tools/plot_sb_development_quality.py',
         'paper/figures/sb_development_quality.pdf', 'paper/figures/sb_development_quality.tex',
         'paper/figures/sb_development_quality.png', 'paper/figures/sb_development_quality.json',
         'tools/render_sb_ex5p_native_STA_paths.py',
         'paper/figures/ex5p_native_endpoint_arrivals.pdf',
         'paper/figures/ex5p_native_endpoint_arrivals.png',
         'paper/figures/ex5p_native_endpoint_arrivals.tex',
         'paper/figures/ex5p_native_endpoint_arrivals.tsv',
         'paper/figures/ex5p_native_endpoint_arrivals.json']
paths.extend(['tools/plot_refreshed_native_quality.py', *['paper/figures/refreshed_native_quality'+ext for ext in ['.tex','.tsv','.pdf','.png','.json']]])
paths.extend(['tools/plot_upstream_hash_native_pairs.py', *['paper/figures/upstream_hash_native_pairs'+ext for ext in ['.tex','.tsv','.pdf','.png','.json']]])
paths.extend(['tools/plot_upstream_hash_three_case_pairs.py', *['paper/figures/upstream_hash_three_case_pairs'+ext for ext in ['.tex','.tsv','.pdf','.png','.json']]])
paths.extend(['tools/plot_width_first_five_quality.py', *['paper/figures/width_first_five_quality'+ext for ext in ['.tex','.tsv','.pdf','.png','.json']]])
paths.extend(['tools/plot_width_all_twelve_quality.py', *['paper/figures/width_all_twelve_quality'+ext for ext in ['.tex','.tsv','.pdf','.png','.json']]])
manifest = dict(status='preliminary_draft_built', command=command,
                artifacts_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths},
                scope='Two-pass LaTeX build and direct draft evidence integrity; not research completion',
                research_complete=False, board_result=False)
(paper/'build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status=manifest['status'],pdf=str(paper/'dieroute.pdf'),research_complete=False)))
