"""Independently check admission-stage HLS screen sources, numeric constraints and interface."""
import hashlib,json,re,xml.etree.ElementTree as E
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_admission_compare_stage_HLS_screen_20261015'
def main():
 refs={}
 def sha(f):
  key=str(f)
  if key not in refs:refs[key]=hashlib.sha256(Path(f).read_bytes()).hexdigest()
  return refs[key]
 protocol=json.loads((P/'protocol.json').read_text());result=json.loads((P/'result.json').read_text())
 for d in [protocol,result,*result['outcomes']]:
  for f,h in d['source_sha256'].items():assert sha(f)==h,f
 assert result['status']=='both_synthesis_screens_complete_report_interpretation_required'
 top='dieroute_native_snapshot_search_sharded_hbm';interfaces=[];rows=[]
 def abi(f):
  s=f.read_text();sha(f);return sorted(re.sub(r'\s+',' ',v.strip()) for v in s.splitlines() if re.match(r'^(input|output|inout)\s',v)),dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',s,re.M))
 for flag in [0,1]:
  d=P/('flag'+str(flag));sol=d/'project/solution1';constraint=sol/'.autopilot/db'/(top+'.constraint.tcl');block=re.search(r'set clock_constraint\s*\{(.*?)\}',constraint.read_text(),re.S);assert block;period=Decimal(re.findall(r'\bperiod\s+([0-9.]+)',block[1])[0]);unc=Decimal(re.findall(r'\buncertainty\s+([0-9.]+)',block[1])[0]);assert (period,unc)==(Decimal('3.333'),Decimal('0.89991'))
  xml=sol/'syn/report'/(top+'_csynth.xml');report=E.parse(xml).getroot();estimate=Decimal(report.findtext('.//EstimatedClockPeriod'));assert estimate<=period-unc;interfaces.append(abi(sol/'syn/verilog'/(top+'.v')))
  helper=None
  if flag:
   f=sol/'syn/report/native_admission_improves_stage_csynth.xml';x=E.parse(f).getroot();lat=x.find('.//SummaryOfOverallLatency');assert lat.findtext('Best-caseLatency')==lat.findtext('Worst-caseLatency')=='2' and lat.findtext('PipelineInitiationInterval')=='1';helper=dict(latency_cycles=2,II=1,estimate_ns=x.findtext('.//EstimatedClockPeriod'));sha(f)
  log=(d/'console.log').read_text();assert 'SHARDED_SEARCH_DIFFERENTIAL calls=10' in log and 'CSim done with 0 errors' in log
  rows.append(dict(flag=flag,estimated_ns=str(estimate),effective_budget_ns=str(period-unc),helper=helper,resources={v.tag:int(v.text) for v in report.find('.//AreaEstimates/Resources')},all_loop_constraints_met='All loop constraints were NOT satisfied' not in log))
  for f in [constraint,xml,d/'console.log']:sha(f)
 original=R/'work/native_higher_g_hls_validation_20261015/snapshot/project/solution1/syn/verilog'/(top+'.v');assert interfaces[0]==interfaces[1]==abi(original);assert (len(interfaces[0][0]),len(interfaces[0][1]))==(290,79)
 for f in [P/'protocol.json',P/'result.json',P/'manifest.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='paired_compare_stage_numeric_HLS_gate_and_achieved2cycleII1_verified',outcomes=rows,external_port_declarations=290,bus_parameters=79,source_sha256=refs,adopted=False,research_complete=False,scope='Independent frozen source/hash, same exact clock budget, generated external interface vs original higher-g snapshot, helper achieved latency/II and10call Csim checks. Both tops report unsatisfied loop constraints, not waived. No RTL co-simulation, full native differential or routed physical timing proof.')
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(report['status'])
if __name__=='__main__':main()
