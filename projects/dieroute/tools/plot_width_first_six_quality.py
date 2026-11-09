"""Plot reviewed posterior observations without presenting unfinished cases as successes."""
import csv,hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def main():
 source=R/'work/width_coverage_first_six_summary_20261018/audit.json';a=json.loads(source.read_text());assert a['reviewed']==6 and a['planned']==12
 for name,h in a['source_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h,name
 rows=a['rows'];labels=['A160','A320','F160','F320','E160','E320'];out=R/'paper/figures';base=out/'width_first_six_quality'
 with base.with_suffix('.tsv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=['case','wirelength_percent','cpd_percent','layer_transition_percent'],delimiter='\t');w.writeheader()
  for v,label in zip(rows,labels):w.writerow({'case':label,'wirelength_percent':v['wirelength_delta_percent'],'cpd_percent':v['cpd_delta_percent'],'layer_transition_percent':v['layer_transition_delta_percent']})
 lines=[r'\documentclass[tikz,border=3pt]{standalone}',r'\usepackage{pgfplots}',r'\usepgfplotslibrary{groupplots}',r'\pgfplotsset{compat=1.18}',r'\begin{document}',r'\begin{tikzpicture}',r'\begin{groupplot}[group style={group size=3 by 1,horizontal sep=1cm},width=5.6cm,height=5.5cm,ybar,/pgf/bar width=9pt,xtick={1,2,3,4,5,6},xticklabels={A160,A320,F160,F320,E160,E320},xticklabel style={rotate=45,anchor=east},enlarge x limits=.16,grid=major,grid style={gray!15},tick label style={font=\scriptsize},label style={font=\small},title style={font=\small}]']
 for title,key in [('Wirelength','wirelength_delta_percent'),('CPD','cpd_delta_percent'),('Layer transitions','layer_transition_delta_percent')]:
  minimum=min(v[key] for v in rows)*1.12
  ylabel=r',ylabel={Change from baseline (\%)}' if title=='Wirelength' else ''
  lines.append(r'\nextgroupplot[title={'+title+'}'+ylabel+',ymin='+str(minimum)+r',ymax=.5]')
  coords=' '.join('('+str(i+1)+','+str(v[key])+')' for i,v in enumerate(rows));lines.append(r'\addplot[fill=blue!60,draw=none] coordinates {'+coords+'};')
 lines += [r'\end{groupplot}',r'\node[anchor=north,font=\scriptsize,align=center] at (current bounding box.south) {Six of 12 posterior configurations, seed1; A: apex2, F: frisc, E: elliptic; suffix: channel width.\\All use 20 by 16 sites. Layer transitions are modeled; no physical SLL or statistical claim.};',r'\end{tikzpicture}',r'\end{document}']
 tex=base.with_suffix('.tex');tex.write_text('\n'.join(lines)+'\n')
 with base.with_suffix('.build.stdout').open('w') as f:subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',str(out),str(tex)],stdout=f,stderr=subprocess.STDOUT,check=True)
 subprocess.run(['pdftoppm','-singlefile','-r','150','-png',str(base.with_suffix('.pdf')),str(base)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();manifest={'status':'six_reviewed_posterior_quality_observations_rendered','source_sha256':{str(p):sha(p) for p in [source,Path(__file__).resolve()]},'artifacts_sha256':{str(base.with_suffix(s)):sha(base.with_suffix(s)) for s in ['.tex','.tsv','.pdf','.png']},'scope':a['scope'],'research_complete':False};base.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n');print(base.with_suffix('.png'))
if __name__=='__main__':main()
