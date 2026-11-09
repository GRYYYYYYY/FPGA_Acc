"""Audit directed HLS/Verilog tests and unchanged external RTL interfaces."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];P=R/'work/native_higher_g_hls_validation_20261015'
def sha(f):
 h=hashlib.sha256()
 with Path(f).open('rb') as v:
  for b in iter(lambda:v.read(1048576),b''):h.update(b)
 return h.hexdigest()
def abi(text):
 ports=sorted(re.sub(r'\s+',' ',line.strip()) for line in text.splitlines() if re.match(r'^(input|output|inout)\s',line))
 params=dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',text,re.M))
 return ports,params

def main():
 p=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='both_HLS_tools_terminal_requires_independent_audit'
 refs={}
 for field in ['source_sha256','prerequisite_sha256']:
  for f,h in p[field].items():assert sha(f)==h,f;refs[f]=h
 for f,h in json.loads((P/'launch_protocol.json').read_text())['source_sha256'].items():assert sha(f)==h,f;refs[f]=h
 rows=[]
 for name,top,parent in [('worker','dieroute_native_search_worker_hbm','native_search_worker_hls_v2_20261014'),('snapshot','dieroute_native_snapshot_search_sharded_hbm','native_snapshot_sharded_hls_v1_20261014')]:
  step=next(v for v in m['steps'] if v['name']==name);assert step['returncode']==0
  d=P/name;sol=d/'project/solution1';xml=sol/'syn/report'/(top+'_csynth.xml');rtl=sol/'syn/verilog'/(top+'.v');cosim=sol/'sim/report'/(top+'_cosim.rpt');log=d/'console.log';text=log.read_text();assert 'C/RTL co-simulation finished: PASS' in text
  assert re.search(r'\|\s*Verilog\s*\|\s*Pass\s*\|',cosim.read_text())
  x=ET.parse(xml).getroot();assert x.findtext('ReportVersion/Version')=='2022.2' and x.findtext('UserAssignments/Part')==p['part'] and x.findtext('UserAssignments/TopModelName')==top
  assert x.findtext('UserAssignments/TargetClockPeriod')=='3.33' and 'create_clock -period 3.333' in (d/'run.tcl').read_text()
  old=R/'work'/parent/'project/solution1/syn/verilog'/(top+'.v');ports,params=abi(rtl.read_text());assert ports and abi(old.read_text())==(ports,params)
  widths={k:int(v) for k,v in re.findall(r'^parameter\s+C_M_AXI_([A-Z0-9_]+)_DATA_WIDTH\s*=\s*(\d+)',rtl.read_text(),re.M)}
  if name=='worker':assert widths=={'SEARCH_MEMORY':512,'TRAFFIC_MEMORY':512} and 'WORKER_HIGHER_G_EQUAL_F calls=8' in text
  else:assert widths=={'AUTHORITY_MEMORY':512,'GRAPH_MEMORY':64,'OWNER0':512,'OWNER1':512,'OWNER2':512,'SCRATCH_MEMORY':512} and 'SHARDED_SEARCH_DIFFERENTIAL calls=10' in text
  resources={v.tag:int(v.text) for v in x.find('AreaEstimates/Resources')};rows.append(dict(component=name,requested_clock_mhz=300,requested_period_ns=3.333,report_rounded_target_ns=3.33,estimated_period_ns=float(x.findtext('PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod')),resources=resources,verilog_cosim='Pass',matching_parent_port_declarations=len(ports),matching_parent_bus_parameters=len(params),axi_data_widths=widths,static_worst_latency=x.findtext('PerformanceEstimates/SummaryOfOverallLatency/Worst-caseLatency')))
  for f in [xml,rtl,old,cosim,log,d/'preflight.stdout']:refs[str(f)]=sha(f)
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',Path(__file__).resolve()]:refs[str(f)]=sha(f)
 report=dict(status='both_higher_g_HLS_components_directed_RTL_pass_external_ABI_unchanged',components=rows,worker_added_equal_f_calls=8,snapshot_directed_search_calls=10,source_sha256=refs,scope='Standalone HLS C simulation/synthesis/Verilog cosimulation, coherent higher-g flag, original directed suites plus explicit equal-f order fixtures. External RTL port declarations and AXI/control bus parameters match parent; synthesis period estimates and undef static latencies retained as such. No linked image, full native RTL run, routed300MHz signoff, XRT, FPGA performance or adoption claim.',adopted=False,board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()
