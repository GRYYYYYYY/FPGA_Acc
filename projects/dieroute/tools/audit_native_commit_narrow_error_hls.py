"""Review narrow internal error RTL, preserving external interface and full command tests."""
import hashlib,json,re,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_narrow_error_hls_20261015'
def main():
 refs={}
 def sha(f):
  f=Path(f).resolve();h=hashlib.sha256(f.read_bytes()).hexdigest();refs[str(f)]=h;return h
 for name in ['protocol.json','launch_protocol.json']:
  for f,h in json.loads((P/name).read_text())['source_sha256'].items():assert sha(f)==h,f
 m=json.loads((P/'manifest.json').read_text());assert m['status']=='HLS_exited_requires_independent_review' and m['returncode']==0,m
 log=(P/'run.log').read_text();assert 'C/RTL co-simulation finished: PASS' in log and 'CSim done with 0 errors' in log
 calls=re.findall(r'SHARDED_DIFFERENTIAL calls=(\d+) isolated_owner_banks=3',log);assert len(calls)>=2 and set(calls)=={'75'},calls
 progress=[tuple(map(int,p)) for p in re.findall(r'RTL Simulation : (\d+) / (\d+)',log)];assert progress and progress[-1]==(75,75),progress[-3:]
 top='dieroute_net_commit_sharded_hbm';sol=P/'project/solution1';xml=sol/'syn/report'/(top+'_csynth.xml');rtl=sol/'syn/verilog'/(top+'.v');cosim=sol/'sim/report'/(top+'_cosim.rpt')
 assert re.search(r'\|\s*Verilog\s*\|\s*Pass\s*\|',cosim.read_text())
 x=ET.parse(xml).getroot();assert x.findtext('ReportVersion/Version')=='2022.2' and x.findtext('UserAssignments/Part')=='xcu280-fsvh2892-2L-e' and x.findtext('UserAssignments/TopModelName')==top
 assert x.findtext('UserAssignments/TargetClockPeriod')=='3.33' and 'create_clock -period 3.333' in (P/'run.tcl').read_text()
 def abi(text):
  ports=sorted(re.sub(r'\s+',' ',line.strip()) for line in text.splitlines() if re.match(r'^(input|output|inout)\s',line))
  params=dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',text,re.M));return ports,params
 parent=R/'work/net_commit_sharded_hls_v3_20261014/project/solution1/syn/verilog'/(top+'.v');a=abi(rtl.read_text());assert a[0] and a==abi(parent.read_text())
 parentxml=parent.parent.parent/'report'/(top+'_csynth.xml');px=ET.parse(parentxml).getroot()
 def metrics(z):return dict(estimated_period_ns=float(z.findtext('PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod')),resources={v.tag:int(v.text) for v in z.find('AreaEstimates/Resources')},worst_static_latency=z.findtext('PerformanceEstimates/SummaryOfOverallLatency/Worst-caseLatency'))
 store=list((sol/'syn/verilog').glob('*store.v'));assert len(store)==1
 width=re.search(r'input\s*\[(\d+):0\] this_error_read;',store[0].read_text());assert width
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'run.log',P/'run.tcl',xml,rtl,cosim,parent,parentxml,store[0],Path(__file__).resolve()]:sha(f)
 report=dict(status='narrow_internal_error75_RTL_calls_pass_external_ABI_matches_parent',rtl_calls=75,matching_port_declarations=len(a[0]),matching_bus_parameters=len(a[1]),store_error_argument_bits=int(width.group(1))+1,parent_HLS=metrics(px),candidate_HLS=metrics(x),source_sha256=refs,scope='Standalone HLS and Verilog command differential. Parent and variant same requested3.333ns. HLS estimates are not routed signoff, and internal width reduction is not proof of timing benefit. No board measurement or adoption.',adopted=False,board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()
