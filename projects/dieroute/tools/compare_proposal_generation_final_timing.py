"""Compare completed requested-clock reports, without inferring board performance."""
from pathlib import Path
import csv,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1]
def main():
 refs={};rows=[]
 def bind(p):
  p=Path(p);v=hashlib.sha256(p.read_bytes()).hexdigest();refs[str(p.resolve())]=v;return v
 parser=R/'tools/audit_proposal_generation_routed_reports.py'
 spec=importlib.util.spec_from_file_location('final_report_parser',parser);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);bind(parser)
 for name,folder in [('scratch_split','scratch_split'),('proposal_generation','proposal_generation')]:
  audit=R/f'work/{folder}_routed_review_20261018/independent_audit.json'
  a=json.loads(audit.read_text());bind(audit)
  assert a['status'] in ['retained_requested_clock_report_checks_failed','retained_requested_clock_report_checks_pass_engineering_review_still_required']
  d=R/f'work/{folder}_postlink_readonly_20261018/reports'
  for filename in ['timing_summary.rpt','kernel_clocks.tsv']:
   p=d/filename;assert bind(p)==a['source_sha256'][str(p)],p
  assert module.timing((d/'timing_summary.rpt').read_text())==a['design_timing_summary']
  clocks=list(csv.DictReader((d/'kernel_clocks.tsv').open(),delimiter='\t'))
  assert {v['cu'] for v in clocks}=={'net_commit','search_worker','snapshot_search'}
  assert all(float(v['period_ns'])==3.333 for v in clocks)
  rows.append({'candidate':name,'timing':a['design_timing_summary'],'checks':a['checks'],'final_clock_topology_mhz':a['final_clock_topology_mhz'],'route':a['route']})
 before,after=[v['timing'] for v in rows]
 result={'status':'two_completed_retained_requested_clock_reports_compared','rows':rows,'wns_delta_ns':after['wns_ns']-before['wns_ns'],'tns_magnitude_reduction_percent':100*(1-abs(after['tns_ns'])/abs(before['tns_ns'])),'setup_failing_endpoint_reduction':before['setup_failing']-after['setup_failing'],'scope':'One implementation per source variant at the retained requested CU period 3.333ns. Different endpoint totals remain explicit. Descriptive comparison does not isolate causality, establish closure, validate adjusted clocks, or demonstrate FPGA acceleration. Effective configured DRC severities include inherited HDPR-5 Warning override; default-severity clearance is not established.','source_sha256':refs,'adopted':False,'board_result':False,'research_complete':False}
 out=R/'work/proposal_generation_final_timing_comparison_20261018';out.mkdir()
 with (out/'audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
