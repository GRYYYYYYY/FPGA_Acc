"""Check achieved local pipeline and external ABI after terminal synthesis."""
import hashlib,json,re,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_filter_probe_pipeline_screen_20261015'
def main():
 m=json.loads((P/'manifest.json').read_text());assert m['status']=='CPU_and_synthesis_terminal_requires_review'
 sol=P/'project/solution1';f=sol/'syn/report/p_anonymous_namespace_journal_filter_probe_csynth.xml';x=E.parse(f)
 assert x.findtext('.//Best-caseLatency')=='2' and x.findtext('.//Worst-caseLatency')=='2' and x.findtext('.//PipelineInitiationInterval')=='1'
 top='dieroute_net_commit_sharded_hbm';rtl=sol/'syn/verilog'/(top+'.v');parent=R/'work/native_commit_two_phase_key_filter_screen_v2_20261015/project/solution1/syn/verilog'/(top+'.v')
 def abi(f):
  s=f.read_text();return sorted(re.sub(r'\s+',' ',v.strip()) for v in s.splitlines() if re.match(r'^(input|output|inout)\s',v)),dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',s,re.M))
 a=abi(rtl);assert a==abi(parent)
 xml=sol/'syn/report'/(top+'_csynth.xml');t=E.parse(xml).findtext('.//EstimatedClockPeriod');assert t=='2.586'
 refs={str(v):hashlib.sha256(v.read_bytes()).hexdigest() for v in [f,xml,rtl,parent,P/'manifest.json',P/'probe_changes.json',Path(__file__).resolve()]}
 report=dict(status='local_probe_latency2_II1_achieved_whole_kernel_timing_worse',helper_estimated_ns=x.findtext('.//EstimatedClockPeriod'),helper_latency=2,helper_II=1,top_estimated_ns=t,external_port_declarations=len(a[0]),bus_parameters=len(a[1]),source_sha256=refs,adopted=False,board_result=False,research_complete=False,interpretation='Scheduling boundary achieved locally but top exceeds unchanged2.43309ns effective budget and prior2.503ns estimate. No proven exact critical-operation cause. No RTL or physical run.')
 with (P/'structure_audit.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(report['status'])
if __name__=='__main__':main()
