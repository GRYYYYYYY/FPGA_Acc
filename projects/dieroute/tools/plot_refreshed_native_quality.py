"""Publication figure for audited incremental CPU quality changes."""
import csv,hashlib,json,subprocess
from decimal import Decimal
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1]
    files=[root/'work/native_joint_budget_net_repair_v2_20261016/independent_audit.json',root/'work/native_refreshed_critical_policy_v1_20261016/independent_audit.json',root/'work/native_refreshed_critical_policy_v1_20261016/protocol.json']
    before={r['case']:r for r in json.loads(files[0].read_text())['outcomes']};after={r['case']:r for r in json.loads(files[1].read_text())['outcomes']};cases=json.loads(files[2].read_text())['cases']
    out=root/'paper/figures';base=out/'refreshed_native_quality';rows=[]
    for case in cases:
        name=case['label'];assert after[name]['joint_baseline_pass']
        row=dict(case=name)
        for metric,key,baseline in [('WL','wirelength',case['baseline_wirelength']),('CPD','cpd_ns',case['baseline_cpd_ns'])]:
            for stage,data in [('v2',before),('refresh',after)]:
                row[metric+'_'+stage]=str((Decimal(str(data[name][key]))/Decimal(str(baseline))-1)*100)
        rows.append(row)
    with base.with_suffix('.tsv').open('w') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
    lines=[r'\documentclass[tikz,border=3pt]{standalone}',r'\usepackage{pgfplots}',r'\usepgfplotslibrary{groupplots}',r'\pgfplotsset{compat=1.18}',r'\begin{document}',r'\begin{tikzpicture}',r'\begin{groupplot}[group style={group size=2 by 1,horizontal sep=1.2cm},width=7cm,height=5cm,ybar,/pgf/bar width=9pt,symbolic x coords={ex5p,diffeq,alu4},xtick=data,enlarge x limits=.25,grid=major,grid style={gray!15},tick label style={font=\small},label style={font=\small},title style={font=\small}]']
    for metric,ymin,ymax in [('WL',-15,1),('CPD',-.6,.9)]:
        lines.append(r'\nextgroupplot[title={'+metric+r' change from native baseline},ylabel={Percent},ymin='+str(ymin)+',ymax='+str(ymax)+r',legend style={font=\scriptsize,at={(.5,1.25)},anchor=south,legend columns=2}]')
        for stage,color in [('v2','blue!60'),('refresh','orange!75')]:
            coords=' '.join('('+r['case']+','+format(Decimal(r[metric+'_'+stage]),'.8f')+')' for r in rows)
            lines.append(r'\addplot[fill='+color+r',draw=none] coordinates {'+coords+r'};')
        if metric=='WL':lines.append(r'\legend{Joint-budget sweep,Refreshed critical paths}')
    lines.extend([r'\end{groupplot}',r'\node[anchor=north,font=\scriptsize,align=center] at (current bounding box.south) {One CPU development execution; incremental refinement of v2 endpoints.\\Ex5p CPD margin: 0.5 ps. No held-out or FPGA speedup claim.};',r'\end{tikzpicture}',r'\end{document}'])
    tex=base.with_suffix('.tex');tex.write_text('\n'.join(lines)+'\n')
    with base.with_suffix('.build.stdout').open('w') as log:subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',str(out),str(tex)],stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run(['pdftoppm','-singlefile','-r','150','-png',str(base.with_suffix('.pdf')),str(base)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    report=dict(status='audited_v2_and_refreshed_quality_figure_rendered',cases=rows,source_sha256={str(p):sha(p) for p in [*files,Path(__file__)]},artifacts_sha256={str(base.with_suffix(s)):sha(base.with_suffix(s)) for s in ['.tex','.tsv','.pdf','.png']},research_complete=False,scope='Percent change versus each design baseline; one CPU incremental development run. No repeated-seed, heldout or FPGA result.')
    base.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(base.with_suffix('.png'))


if __name__=='__main__':main()
