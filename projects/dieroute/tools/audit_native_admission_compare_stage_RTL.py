"""Review new admission-stage RTL with exact timing constraints and external ABI."""
import hashlib,json,re,xml.etree.ElementTree as E
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_admission_compare_stage_RTL_20261015';B=R/'work/native_admission_compare_stage_HLS_screen_20261015'
def main():
 refs={}
 def sha(f):
  key=str(f)
  if key not in refs:refs[key]=hashlib.sha256(Path(f).read_bytes()).hexdigest()
  return refs[key]
 protocol=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='HLS_RTL_tool_terminal_requires_independent_audit' and m['returncode']==0
 for f,h in protocol['source_sha256'].items():assert sha(f)==h,f
 for f in (P/'source').iterdir():
  if f.is_file():assert f.read_bytes()==(B/'flag1/source'/f.name).read_bytes(),f
 sol=P/'project/solution1';top='dieroute_native_snapshot_search_sharded_hbm';xml=sol/'syn/report'/(top+'_csynth.xml');x=E.parse(xml).getroot();constraint=sol/'.autopilot/db'/(top+'.constraint.tcl');block=re.search(r'set clock_constraint\s*\{(.*?)\}',constraint.read_text(),re.S);assert block;period=Decimal(re.findall(r'\bperiod\s+([0-9.]+)',block[1])[0]);unc=Decimal(re.findall(r'\buncertainty\s+([0-9.]+)',block[1])[0]);assert (period,unc)==(Decimal('3.333'),Decimal('0.89991'));estimate=Decimal(x.findtext('.//EstimatedClockPeriod'));assert estimate<=period-unc
 h=sol/'syn/report/native_admission_improves_stage_csynth.xml';helper=E.parse(h).getroot();lat=helper.find('.//SummaryOfOverallLatency');assert lat.findtext('Best-caseLatency')==lat.findtext('Worst-caseLatency')=='2' and lat.findtext('PipelineInitiationInterval')=='1'
 def abi(f):
  sha(f);s=f.read_text();return sorted(re.sub(r'\s+',' ',v.strip()) for v in s.splitlines() if re.match(r'^(input|output|inout)\s',v)),dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',s,re.M))
 rtl=sol/'syn/verilog'/(top+'.v');a=abi(rtl);assert a==abi(B/'flag0/project/solution1/syn/verilog'/(top+'.v'));assert (len(a[0]),len(a[1]))==(290,79)
 log=(P/'console.log').read_text();assert 'C/RTL co-simulation finished: PASS' in log and 'SHARDED_SEARCH_DIFFERENTIAL calls=10' in log;progress=re.findall(r'RTL Simulation : (\d+) / (\d+)',log);assert progress and progress[-1]==('10','10');cosim=sol/'sim/report'/(top+'_cosim.rpt');assert re.search(r'\|\s*Verilog\s*\|\s*Pass\s*\|',cosim.read_text())
 for f in [xml,constraint,h,cosim,P/'console.log',P/'protocol.json',P/'manifest.json',Path(__file__).resolve()]:sha(f)
 result=dict(status='admission_stage10_Verilog_calls_exact_numeric_gate_and_ABI_verified',RTL_calls=10,estimated_ns=str(estimate),effective_budget_ns=str(period-unc),helper_estimated_ns=helper.findtext('.//EstimatedClockPeriod'),helper_latency_cycles=2,helper_II=1,external_ports=290,bus_parameters=79,source_sha256=refs,adopted=False,research_complete=False,scope='Same enabled stage source as paired screen, original10call higher-g snapshot fixture, exact2.43309ns budget and original external ABI. Not fullgraph RTL/XRT or physical setup proof; unmet-loop warnings retained by screen audit.')
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(result['status'])
if __name__=='__main__':main()
