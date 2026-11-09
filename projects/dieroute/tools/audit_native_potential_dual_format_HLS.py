"""Numeric timing, generated external ABI and directed dual-format RTL review."""
import hashlib,json,re,xml.etree.ElementTree as E
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_potential_dual_format_HLS_20261015'
def main():
 refs={}
 def sha(f):
  p=Path(f);refs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return refs[str(p)]
 x=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='HLS_terminal_requires_numeric_ABI_and_RTL_review' and m['returncode']==0,m
 for f,h in x['source_sha256'].items():assert sha(f)==h,f
 extension=json.loads((P/'fixture_extension.json').read_text());parent=Path(extension['parent']);assert sha(parent)==extension['parent_sha256'];text=(P/'source/native_snapshot_search_hbm_tb.cpp').read_text();added=extension['insert_before_final_main_brace'];assert text.count(added)==1 and text.replace(added,'',1)==parent.read_text()
 sol=P/'project/solution1';top='dieroute_native_snapshot_search_sharded_hbm';xml=sol/'syn/report'/(top+'_csynth.xml');report=E.parse(xml);estimate=Decimal(report.findtext('.//EstimatedClockPeriod'))
 constraint=sol/'.autopilot/db'/(top+'.constraint.tcl');block=re.search(r'set clock_constraint\s*\{(.*?)\}',constraint.read_text(),re.S).group(1)
 def value(key):return Decimal(re.search(r'\b'+key+r'\s+([0-9.]+)',block).group(1))
 period=value('period');uncertainty=value('uncertainty');budget=period-uncertainty;assert period==Decimal('3.333') and uncertainty==Decimal('0.89991')
 def abi(f):
  s=f.read_text();return sorted(re.sub(r'\s+',' ',v.strip()) for v in s.splitlines() if re.match(r'^(input|output|inout)\s',v)),dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',s,re.M))
 rtl=sol/'syn/verilog'/(top+'.v');old=R/'work/native_higher_g_hls_validation_20261015/snapshot/project/solution1/syn/verilog'/(top+'.v');a=abi(rtl);assert a==abi(old)
 tcl=(P/'run.tcl').read_text();assert all('DIEROUTE_NATIVE_HIGHER_G_TIE=1' in v and 'DIEROUTE_NATIVE_PACKED_POTENTIAL8=1' in v for v in tcl.splitlines() if v.startswith('add_files'))
 log=(P/'console.log').read_text();assert 'CSim done with 0 errors' in log and 'SHARDED_SEARCH_DIFFERENTIAL calls=25' in log and 'DUAL_FORMAT_ADDITIONAL calls=15' in log
 passed=estimate<=budget
 if passed:
  assert 'C/RTL co-simulation finished: PASS' in log
  progress=re.findall(r'RTL Simulation : (\d+) / (\d+)',log);assert progress and progress[-1]==('25','25')
  cosim=sol/'sim/report'/(top+'_cosim.rpt');assert re.search(r'\|\s*Verilog\s*\|\s*Pass\s*\|',cosim.read_text());sha(cosim)
 else:assert 'NUMERIC_EFFECTIVE_TIMING_REJECT_NO_COSIM' in log and 'C/RTL co-simulation finished: PASS' not in log
 for f in [xml,constraint,rtl,old,P/'console.log',P/'protocol.json',P/'manifest.json',P/'fixture_extension.json',P/'run.tcl',Path(__file__).resolve()]:sha(f)
 result=dict(status='dual_format25_Verilog_calls_numeric_timing_and_external_ABI_pass' if passed else 'dual_format_CSIM25_pass_numeric_timing_failed_no_RTL',requested_ns=str(period),uncertainty_ns=str(uncertainty),effective_budget_ns=str(budget),estimated_ns=str(estimate),reported_estimate_pass=passed,RTL_calls=25 if passed else 0,original_directed_calls=10,new_packed_cases=15,external_port_declarations=len(a[0]),bus_parameters=len(a[1]),resources={v.tag:int(v.text) for v in report.find('.//AreaEstimates/Resources')},source_sha256=refs,adopted=False,board_result=False,research_complete=False,scope='Enabled dualformat runtime config0/1/2, original10wide/infinity cases unchanged plus6packed tie lanes,8nonzero sink lanes,1invalidformat. Same3.333ns constraint, exact numeric effective gate. Generated interface compared to original higher-g snapshot. Not fullgraph RTL, XRT, routed or board proof.')
 with (P/'independent_audit.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
