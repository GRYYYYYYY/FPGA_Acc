"""Render completed audited matched CPU pairs; never render partial-run estimates."""
import argparse,csv,hashlib,json,subprocess
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parents[1]
SOURCE=R/'work/upstream_target_hash_native_pairs_20261018/independent_pair_audit.json'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check-only',action='store_true');args=p.parse_args()
 if args.check_only:
  print(json.dumps({'completed_pair_audit_available':SOURCE.is_file(),'render_started':False}));return
 a=json.loads(SOURCE.read_text());assert a['status']=='ten_native_runs_outputs_equivalent_and_matched_process_times_reviewed'
 pairs=a['pairs'];assert len(pairs)==5 and [v['pair'] for v in pairs]==list(range(5))
 rows=[{'pair':v['pair']+1,'parent_seconds':str(Decimal(v['parent_ns'])/10**9),'candidate_seconds':str(Decimal(v['candidate_ns'])/10**9)} for v in pairs]
 out=R/'paper/figures';out.mkdir(exist_ok=True);base=out/'upstream_hash_native_pairs'
 with base.with_suffix('.tsv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
 lines=[r'\documentclass[tikz,border=3pt]{standalone}',r'\usepackage{pgfplots}',r'\pgfplotsset{compat=1.18}',r'\begin{document}',r'\begin{tikzpicture}',r'\begin{axis}[width=12cm,height=6cm,ybar,bar width=10pt,ymin=0,xlabel={Matched pair},ylabel={Complete process time (s)},xtick={1,2,3,4,5},enlarge x limits=.14,grid=major,grid style={gray!15},legend style={at={(.5,1.02)},anchor=south,legend columns=2,font=\small}]']
 for key,color in [('parent_seconds','blue!60'),('candidate_seconds','orange!75')]:
  coords=' '.join('('+str(v['pair'])+','+v[key]+')' for v in rows);lines.append(r'\addplot[fill='+color+r',draw=none] coordinates {'+coords+'};')
 lines += [r'\legend{Ordered target set,Hash target set}',r'\end{axis}',r'\node[anchor=north,font=\scriptsize,align=center] at (current bounding box.south) {One ex5p development case; shared host; five alternating-order pairs.\\Includes persistent STA startup/shutdown. No FPGA speedup claim.};',r'\end{tikzpicture}',r'\end{document}']
 tex=base.with_suffix('.tex');tex.write_text('\n'.join(lines)+'\n')
 with base.with_suffix('.build.stdout').open('w') as log:subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',str(out),str(tex)],stdout=log,stderr=subprocess.STDOUT,check=True)
 subprocess.run(['pdftoppm','-singlefile','-r','150','-png',str(base.with_suffix('.pdf')),str(base)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 report={'status':'five_audited_native_CPU_pairs_rendered','rows':rows,'source_sha256':{str(p):sha(p) for p in [SOURCE,Path(__file__).resolve()]},'artifacts_sha256':{str(base.with_suffix(s)):sha(base.with_suffix(s)) for s in ['.tex','.tsv','.pdf','.png']},'scope':'Complete wrapper process time on one development case; shared-host/caching effects retained. No cross-case generalization, adoption or physical FPGA claim.','research_complete':False};base.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(base.with_suffix('.png'))
if __name__=='__main__':main()
