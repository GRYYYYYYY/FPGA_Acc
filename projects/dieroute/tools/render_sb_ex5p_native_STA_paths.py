"""Render native endpoint timing with installed PGFPlots, keeping raw data export."""
import argparse,hashlib,json,re,subprocess
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb_ex5p_native_STA_path_alignment_20261015';A=P/'independent_audit.json'
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--pdflatex',default='pdflatex');args=parser.parse_args();x=json.loads(A.read_text());assert x['status']=='three_ex5p_native_STA_reports_reproduced_and63endpoints_aligned'
 paths={label:{v['endpoint']:v for v in rows} for label,rows in x['paths'].items()};endpoints=sorted(paths['baseline'],key=lambda v:int(re.search(r'o_(\d+)_',v)[1]));ids=[int(re.search(r'o_(\d+)_',v)[1]) for v in endpoints]
 out=R/'paper/figures';out.mkdir(exist_ok=True);base=out/'ex5p_native_endpoint_arrivals';table=['endpoint\tbaseline_ns\tweight128_ns\tweight0_ns\tweight128_delta_ns\tweight0_delta_ns']
 for e,n in zip(endpoints,ids):
  values=[Decimal(paths[label][e]['arrival_ns']) for label in ['baseline','weight128','weight0']];table.append('\t'.join(map(str,[n,*values,values[1]-values[0],values[2]-values[0]])))
 base.with_suffix('.tsv').write_text('\n'.join(table)+'\n')
 lines=[r'\documentclass[tikz,border=4pt]{standalone}',r'\usepackage{pgfplots}',r'\usepgfplotslibrary{groupplots}',r'\pgfplotsset{compat=1.18}',r'\definecolor{routeblue}{RGB}{0,114,178}',r'\definecolor{routeorange}{RGB}{213,94,0}',r'\pdfinfoomitdate=1',r'\pdftrailerid{}',r'\begin{document}',r'\begin{tikzpicture}',r'\begin{groupplot}[group style={group size=1 by 2,vertical sep=.65cm},width=6.9in,height=2.15in,xmin='+str(min(ids)-.5)+',xmax='+str(max(ids)+.5)+r',grid=major,grid style={gray!18},tick label style={font=\small},label style={font=\small}]',r'\nextgroupplot[ylabel={Selected worst arrival (ns)},title={ex5p: fixed-route native STA at 63 output endpoints},title style={font=\small,yshift=1.8em},xticklabels=\empty,legend style={at={(.5,1.03)},anchor=south,font=\scriptsize,draw=none,fill=none},legend columns=3]']
 for label,color,title in [('baseline','gray','Native baseline'),('weight128','routeblue','Seed weight 128'),('weight0','routeorange','Seed weight 0')]:
  coordinates=' '.join('('+str(n)+','+paths[label][e]['arrival_ns']+')' for e,n in zip(endpoints,ids));lines += [r'\addplot['+color+r',mark=*,mark size=.7pt,line width=.5pt] coordinates {'+coordinates+r'};',r'\addlegendentry{'+title+'}']
 lines += [r'\nextgroupplot[xlabel={Output endpoint number},ylabel={Difference from baseline (ns)}]',r'\addplot[gray,dashed,forget plot] coordinates {('+str(min(ids))+',0) ('+str(max(ids))+',0)};']
 for label,color in [('weight128','routeblue'),('weight0','routeorange')]:
  coordinates=' '.join('('+str(n)+','+str(Decimal(paths[label][e]['arrival_ns'])-Decimal(paths['baseline'][e]['arrival_ns']))+')' for e,n in zip(endpoints,ids));lines.append(r'\addplot['+color+r',mark=*,mark size=.7pt,line width=.5pt] coordinates {'+coordinates+r'};')
 lines += [r'\end{groupplot}',r'\end{tikzpicture}',r'\end{document}'];base.with_suffix('.tex').write_text('\n'.join(lines)+'\n')
 with base.with_suffix('.build.stdout').open('w') as log:subprocess.run([args.pdflatex,'-interaction=nonstopmode','-halt-on-error','-output-directory',str(out),str(base.with_suffix('.tex'))],stdout=log,stderr=subprocess.STDOUT,check=True)
 subprocess.run(['pdftoppm','-singlefile','-r','150','-png',str(base.with_suffix('.pdf')),str(base)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 files=[base.with_suffix(suffix) for suffix in ['.tex','.tsv','.pdf','.png']];receipt=dict(status='native_STA63endpoint_plot_rendered',source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [A,Path(__file__).resolve(),P/'plot_attempt1.py',P/'plot_attempt1.json']},artifacts={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},scope='Three fixed legal ex5p routes, one selected worst path per endpoint with possibly different starts; printed resolution0.001ns. No all-path or U280 physical timing claim. First missing-Matplotlib attempt retained; installedPGFPlots used without data changes.',board_result=False,research_complete=False)
 base.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
if __name__=='__main__':main()
