"""Render per-case normalized native quality with the installed PGFPlots toolchain."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pdflatex',default='pdflatex');args=parser.parse_args()
 source=ROOT/'work/sb_three_layer_development_matched_20261015/interpretation.json';data=json.loads(source.read_text());assert not data['all_development_gates_pass']
 for q,h in data['source_sha256'].items():assert sha(q)==h,q
 out=ROOT/'paper/figures';base=out/'sb_development_quality';tex=base.with_suffix('.tex')
 lines=[r'\documentclass[tikz,border=4pt]{standalone}',r'\usepackage{pgfplots}',r'\pgfplotsset{compat=1.18}',r'\pdfinfoomitdate=1',r'\pdftrailerid{}',r'\begin{document}',r'\begin{tikzpicture}',r'\begin{axis}[width=6.7in,height=4.2in,xmin=.84,xmax=1.08,ymin=.975,ymax=1.055,grid=major,grid style={gray!15},xlabel={Wirelength / native baseline of each case},ylabel={CPD / native baseline of each case},title={Remaining tail: native development quality},title style={font=\small},tick label style={font=\small},label style={font=\small}]',r'\path[fill=green!8,draw=none] (axis cs:.84,.975) rectangle (axis cs:1,1);',r'\addplot[gray,dashed,forget plot] coordinates {(1,.975) (1,1.055)};',r'\addplot[gray,dashed,forget plot] coordinates {(.84,1) (1.08,1)};',r'\addplot[only marks,mark=x,gray,mark size=3pt] coordinates {(1,1)};',r'\node[anchor=south west,font=\scriptsize,text=gray] at (axis cs:1.002,1.002) {Native baseline};']
 labels={'ex5p':(1.035,1.049,'north east','red!75!black'),'diffeq':(.845,1.012,'north west','blue!70!black'),'alu4':(.965,.981,'south west','orange!80!black')}
 for r in data['cases']:
  x,y=r['wirelength_ratio'],r['cpd_ratio'];name=r['case'];lx,ly,anchor,color=labels[name]
  lines.append(r'\addplot[only marks,mark=*,mark size=3pt,'+color+r'] coordinates {('+f'{x:.10f},{y:.10f}'+r')};')
  lines.append(r'\draw[thin,'+color+r'] (axis cs:'+f'{x:.10f},{y:.10f}'+r') -- (axis cs:'+f'{lx},{ly}'+r');')
  label=name+r'\\'+f'${(x-1)*100:+.2f}'+r'\%$ WL / '+f'${(y-1)*100:+.2f}'+r'\%$ CPD'
  lines.append(r'\node[anchor='+anchor+',text='+color+r',font=\scriptsize] at (axis cs:'+f'{lx},{ly}'+r') {\shortstack{'+label+r'}};')
 lines.extend([r'\node[anchor=south west,text=green!40!black,font=\scriptsize] at (axis cs:.842,.976) {WL and CPD do not increase};',r'\end{axis}',r'\node[anchor=north,font=\scriptsize] at (current bounding box.south) {One run per case; all legal; crossings do not increase; no adoption.};',r'\end{tikzpicture}',r'\end{document}'])
 tex.write_text('\n'.join(lines)+'\n');cmd=[args.pdflatex,'-interaction=nonstopmode','-halt-on-error','-output-directory',str(out),str(tex)]
 with base.with_suffix('.build.stdout').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 subprocess.run(['pdftoppm','-singlefile','-r','150','-png',str(base.with_suffix('.pdf')),str(base)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 files=[base.with_suffix(ext) for ext in ['.tex','.pdf','.png']];report=dict(status='three_case_native_quality_normalized_plot_rendered',cases=data['cases'],source_sha256={str(q):sha(q) for q in [source,Path(__file__).resolve(),ROOT/'work/sb_quality_plot_preparation_20261015/attempt1.json']},artifacts={str(q):sha(q) for q in files},scope='Onecandidatepointpercase,normalizedtoeachnativebaseline. GreenregiononlyWL/CPD;allthreelegal/crossingchecksfromsource. NotcrosscaseParetodominance,repeat,adoptionorphysicalclaim. Matplotlibattemptretained;installedPGFPlotsusedwithoutchangingdata.',board_result=False,research_complete=False)
 base.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],png=str(base.with_suffix('.png')))))
if __name__=='__main__':main()
