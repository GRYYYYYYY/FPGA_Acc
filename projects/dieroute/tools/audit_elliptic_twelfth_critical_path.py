"""Compare archived native worst paths; do not rerun or alter the frozen cohort."""
import hashlib,json,re
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LABEL='elliptic_28x22_cw320_seed1'
BASE=ROOT/'work/width_coverage_roundtrip_20261017'/LABEL/'native_validation/report_timing.setup.rpt'
CAND=ROOT/'work/width_coverage_parents_20261018/parents'/LABEL/'native_validation/report_timing.setup.rpt'
SUMMARY=ROOT/'work/width_coverage_all_twelve_summary_20261020/audit.json'
OUT=ROOT/'work/elliptic_twelfth_critical_path_diagnosis_20261020'
def parse(path):
 text=path.read_text();assert '# Output precision: 3' in text
 block=text.split('#Path 1\n',1)[1].split('#Path 2\n',1)[0]
 data=block.split('Point ',1)[1].split('data arrival time',1)[0]
 points=[]
 for line in data.splitlines():
  m=re.match(r'^(.*?)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$',line)
  if m:points.append((m[1].strip(),Decimal(m[2]),Decimal(m[3])))
 return dict(start=re.search(r'Startpoint:\s*(.*)',block)[1],end=re.search(r'Endpoint\s*:\s*(.*)',block)[1],arrival=Decimal(re.search(r'data arrival time\s+(\d+\.\d+)',block)[1]),points=points)
def main():
 a,b=parse(BASE),parse(CAND)
 assert (a['start'],a['end'])==(b['start'],b['end'])
 assert [p[0] for p in a['points']]==[p[0] for p in b['points']]
 diffs=[dict(point=x[0],baseline_incr_ns=str(x[1]),candidate_incr_ns=str(y[1]),delta_ps=str((y[1]-x[1])*1000)) for x,y in zip(a['points'],b['points']) if x[1]!=y[1]]
 assert len(diffs)==5 and all('.in[' in r['point'] for r in diffs)
 summary=json.loads(SUMMARY.read_text());row=next(r for r in summary['rows'] if r['label']==LABEL)
 assert not summary['research_complete'] and row['cpd_ns']==10.4245
 assert b['arrival']-a['arrival']==Decimal('.004')
 OUT.mkdir(exist_ok=False)
 result=dict(status='archived_same_worst_logic_path_routing_arc_differences_localized',startpoint=a['start'],endpoint=a['end'],baseline_arrival_ns=str(a['arrival']),candidate_arrival_ns=str(b['arrival']),printed_arrival_delta_ps='4.000',changed_printed_input_arcs=diffs,printed_arc_delta_sum_ps=str(sum(Decimal(r['delta_ps']) for r in diffs)),scope='Worst path only, native model at 1ps printed precision. Increment rounding is independent of cumulative arrival rounding; differences do not identify a physical SLL or prove algorithmic causality. Frozen 12-case outcome remains 11joint passes,1CPD regression. No repair or rerun performed.',source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE,CAND,SUMMARY,Path(__file__).resolve()]},research_complete=False)
 (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
