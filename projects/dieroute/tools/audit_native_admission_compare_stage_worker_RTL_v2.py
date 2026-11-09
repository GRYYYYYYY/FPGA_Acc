"""Independent eight-call worker RTL and helper/ABI review."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as E
from decimal import Decimal
R=Path(__file__).resolve().parents[1];P=R/'work/native_admission_compare_stage_worker_RTL_20261015';B=R/'work/native_higher_g_hls_validation_20261015/worker'
def main():
 refs={}
 def sha(f):
  k=str(f)
  if k not in refs:refs[k]=hashlib.sha256(Path(f).read_bytes()).hexdigest()
  return refs[k]
 p=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='HLS_RTL_tool_terminal_requires_independent_audit' and m['returncode']==0
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 for f in (P/'source').iterdir():
  if f.is_file():
   old=R/'work/native_admission_compare_stage_CPU_20261015/source'/f.name if f.name=='native_search_hbm_admission.hpp' else B/'source'/f.name
   assert f.read_bytes()==old.read_bytes();sha(old)
 sol=P/'project/solution1';top='dieroute_native_search_worker_hbm';xml=sol/'syn/report'/(top+'_csynth.xml');x=E.parse(xml).getroot();c=sol/'.autopilot/db'/(top+'.constraint.tcl');b=re.search(r'set clock_constraint\s*\{(.*?)\}',c.read_text(),re.S);assert b;period=Decimal(re.findall(r'\bperiod\s+([0-9.]+)',b[1])[0]);unc=Decimal(re.findall(r'\buncertainty\s+([0-9.]+)',b[1])[0]);assert (period,unc)==(Decimal('3.333'),Decimal('0.89991'));estimate=Decimal(x.findtext('.//EstimatedClockPeriod'));assert estimate<=period-unc
 h=sol/'syn/report/native_admission_improves_stage_csynth.xml';hx=E.parse(h).getroot();lat=hx.find('.//SummaryOfOverallLatency');assert lat.findtext('Best-caseLatency')==lat.findtext('Worst-caseLatency')=='2' and lat.findtext('PipelineInitiationInterval')=='1'
 def abi(f):
  sha(f);s=f.read_text();return sorted(re.sub(r'\s+',' ',v.strip()) for v in s.splitlines() if re.match(r'^(input|output|inout)\s',v)),dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',s,re.M))
 a=abi(sol/'syn/verilog'/(top+'.v'));assert a==abi(B/'project/solution1/syn/verilog'/(top+'.v'))
 log=(P/'console.log').read_text();assert 'C/RTL co-simulation finished: PASS' in log and 'WORKER_HIGHER_G_EQUAL_F calls=8' in log;progress=re.findall(r'RTL Simulation : (\d+) / (\d+)',log);assert progress and progress[-1]==('22','22');cosim=sol/'sim/report'/(top+'_cosim.rpt');assert re.search(r'\|\s*Verilog\s*\|\s*Pass\s*\|',cosim.read_text())
 for f in [xml,c,h,cosim,P/'console.log',P/'protocol.json',P/'manifest.json',Path(__file__).resolve()]:sha(f)
 out=dict(status='admission_stage_worker22RTL_calls_numeric_gate_2cycleII1_and_ABI_verified',RTL_calls=22,equal_f_subset_calls=8,estimate_ns=str(estimate),effective_budget_ns=str(period-unc),helper_cycles=2,helper_II=1,external_ports=len(a[0]),bus_parameters=len(a[1]),source_sha256=refs,adopted=False,research_complete=False,scope='Producer protocol named8call from equal-f marker; actual RTL progress22of22 proves complete fixture. Initial review incorrectly expected8total and failed before output. Same original higherg worker fixture14legacy plus8equal-f calls, only admission-stage header changed; numeric exactbudget, achieved helper latency/II and externalRTL interface match. Not fullgraph RTL/XRT or routed physical proof.')
 with (P/'independent_audit.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'])
if __name__=='__main__':main()
