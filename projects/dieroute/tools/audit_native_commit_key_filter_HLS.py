"""Review enabled-key-filter two-suite RTL and fixed-model cycle comparisons."""
import hashlib,json,re,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_key_filter_HLS_20261015'
def main():
 refs={}
 def sha(f):h=hashlib.sha256(Path(f).read_bytes()).hexdigest();refs[str(f)]=h;return h
 for name in ['protocol.json','launch_protocol.json']:
  for f,h in json.loads((P/name).read_text())['source_sha256'].items():assert sha(f)==h,f
 m=json.loads((P/'manifest.json').read_text());assert m['status']=='both_HLS_terminal_requires_review' and len(m['steps'])==2 and all(v['returncode']==0 for v in m['steps'])
 def abi(text):return sorted(re.sub(r'\s+',' ',v.strip()) for v in text.splitlines() if re.match(r'^(input|output|inout)\s',v)),dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',text,re.M))
 def cycles(f):
  line=next(v for v in f.read_text().splitlines() if re.search(r'\|\s*Verilog\s*\|',v));fields=[v.strip() for v in line.split('|')[1:-1]];assert fields[1]=='Pass';values=list(map(int,fields[2:]));assert len(values)==7;return dict(zip(['latency_min','latency_avg','latency_max','interval_min','interval_avg','interval_max','total'],values))
 rows=[];top='dieroute_net_commit_sharded_hbm'
 for name,calls,parent in [('small',75,'net_commit_sharded_hls_v3_20261014'),('large',45,'native_commit_42path_256reads_RTL_diagnostic_v2_20261015')]:
  d=P/name;sol=d/'project/solution1';log=(d/'console.log').read_text();assert 'CSim done with 0 errors' in log and 'C/RTL co-simulation finished: PASS' in log and log.count(f'SHARDED_DIFFERENTIAL calls={calls} isolated_owner_banks=3')>=2
  progress=[tuple(map(int,v)) for v in re.findall(r'RTL Simulation : (\d+) / (\d+)',log)];assert progress and progress[-1]==(calls,calls)
  if name=='large':assert log.count('LARGE_COMMIT_PROTOCOL calls=45 readset=256 path_nodes=42 owners=3 revision=2')>=2
  tcl=(d/'run.tcl').read_text();assert 'create_clock -period 3.333' in tcl and all('DIEROUTE_COMMIT_KEY_FILTER=1' in v for v in tcl.splitlines() if v.startswith('add_files'))
  assert (d/'source/net_commit_sharded_hbm.cpp').read_text().startswith('#if DIEROUTE_COMMIT_KEY_FILTER != 1')
  xml=sol/'syn/report'/(top+'_csynth.xml');rtl=sol/'syn/verilog'/(top+'.v');cosim=sol/'sim/report'/(top+'_cosim.rpt');base=R/'work'/parent/'project/solution1';x=E.parse(xml).getroot();assert x.findtext('UserAssignments/Part')=='xcu280-fsvh2892-2L-e' and x.findtext('UserAssignments/TargetClockPeriod')=='3.33'
  a=abi(rtl.read_text());assert a==abi((base/'syn/verilog'/(top+'.v')).read_text())
  rows.append(dict(suite=name,RTL_calls=calls,estimated_period_ns=float(x.findtext('.//EstimatedClockPeriod')),resources={v.tag:int(v.text) for v in x.find('.//AreaEstimates/Resources')},effective_HLS_timing_warning='HLS 200-871' in log,external_port_declarations=len(a[0]),bus_parameters=len(a[1]),baseline_cosim_cycles=cycles(base/'sim/report'/(top+'_cosim.rpt')),enabled_cosim_cycles=cycles(cosim)))
  for f in [xml,rtl,cosim,d/'console.log',base/'sim/report'/(top+'_cosim.rpt'),base/'syn/verilog'/(top+'.v')]:sha(f)
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='enabled_key_filter120_Verilog_calls_external_ABI_reviewed',suites=rows,source_sha256=refs,scope='Original75 andcompact300node/256reads/42path45 RTL cases with enabled256bit one-sidedfilter, fixed3.333ns. Functional pass and HLS timing warnings reported separately. Cosim cycles are standalone identical-test/model observations, not fullgraph XRT time, routed/board performance or causal explanation of earlier timeouts. No adoption.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()
