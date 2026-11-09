"""Verify source-bound HLS/RTL evidence and the exported 27-argument ABI."""
import argparse,hashlib,json,re,xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(out,expected_calls):
 out=Path(out);manifest=json.loads((out/'manifest.json').read_text());assert manifest['status']=='passed' and manifest['returncode']==0 and manifest['sources_unchanged']
 for p,h in manifest['source_sha256'].items():assert sha(out/'source'/p)==h
 log=(out/'run.log').read_text();assert 'C/RTL co-simulation finished: PASS' in log and 'CSim done with 0 errors' in log
 observed=[tuple(map(int,x)) for x in re.findall(r'RTL Simulation : (\d+) / (\d+)',log)];assert observed and observed[-1]==(expected_calls,expected_calls) and {x[1] for x in observed}=={expected_calls}
 report=out/'project/u280/syn/report/dieroute_net_commit_hbm_csynth.xml';x=ET.parse(report).getroot()
 assert x.findtext('ReportVersion/Version')=='2022.2' and x.findtext('UserAssignments/Part')==manifest['part']=='xcu280-fsvh2892-2L-e'
 assert x.findtext('UserAssignments/TopModelName')=='dieroute_net_commit_hbm'
 cosim=out/'project/u280/sim/report/dieroute_net_commit_hbm_cosim.rpt'
 line=next(s for s in cosim.read_text().splitlines() if re.search(r'\|\s*Verilog\s*\|',s));columns=[s.strip() for s in line.split('|')[1:-1]];assert columns[1]=='Pass'
 cycles=list(map(int,columns[2:]));assert len(cycles)==7
 def number(name):return Decimal(x.findtext('.//'+name))
 target=number('TargetClockPeriod');uncertainty=number('ClockUncertainty');estimate=number('EstimatedClockPeriod');budget=target-uncertainty
 assert target==4 and uncertainty==Decimal('1.08')
 area=x.find('.//AreaEstimates/Resources');resources={e.tag:int(e.text) for e in area}
 xo=out/'project/dieroute_net_commit_hbm.xo'
 with ZipFile(xo) as z:
  kernel=ET.fromstring(z.read('dieroute_net_commit_hbm/kernel.xml')).find('kernel')
  assert kernel.get('name')=='dieroute_net_commit_hbm' and kernel.get('hwControlProtocol')=='ap_ctrl_chain'
  assert hashlib.sha256(z.read('dieroute_net_commit_hbm/cpu_sources/net_commit_hbm.cpp')).hexdigest()==manifest['source_sha256']['src/net_commit_hbm.cpp']
  ports={p.get('name'):int(p.get('dataWidth')) for p in kernel.find('ports') if p.get('mode')=='master'}
  assert ports=={'M_AXI_TRAFFIC':512,'M_AXI_GRAPH':64,'M_AXI_AUTHORITY':512}
  names='command policy offsets arcs reads shadows branches paths resources trees nets control scratch deltas completion node_count arc_count dies shard_capacity net_capacity tree_capacity read_capacity shadow_capacity branch_capacity path_capacity scratch_capacity delta_capacity'.split()
  args=list(kernel.find('args'));assert len(args)==len(names)==27
  for i,(name,arg) in enumerate(zip(names,args)):
   assert arg.get('name')==name and int(arg.get('id'))==i and int(arg.get('addressQualifier'))==int(i<15)
   expected='M_AXI_GRAPH' if i in (1,2,3) else 'M_AXI_AUTHORITY' if i in (8,9,10,11) else 'M_AXI_TRAFFIC' if i<15 else 'S_AXI_CONTROL'
   assert arg.get('port')==expected and int(arg.get('size'),0)==(8 if i<15 or i==16 else 4)
 rtl=out/'project/u280/syn/verilog/dieroute_net_commit_hbm.v';text=rtl.read_text()
 for name,width in ports.items():assert re.search(r'C_'+name+r'_DATA_WIDTH\s*=\s*'+str(width)+r'\s*;',text)
 if estimate<=budget:assert 'HLS 200-871' not in log
 result=dict(schema='dieroute.net_commit_hls_audit.v1',status='verified' if estimate<=budget else 'timing_gate_failed',c_rtl_pass=True,rtl_calls=expected_calls,target_ns=float(target),uncertainty_ns=float(uncertainty),effective_budget_ns=float(budget),estimated_period_ns=float(estimate),resources=resources,master_ports=ports,arguments=27,xo_sha256=sha(xo),source_sha256=manifest['source_sha256'],cosim_cycles=dict(zip(('latency_min','latency_avg','latency_max','interval_min','interval_avg','interval_max','total'),cycles)),evidence_sha256={str(p.relative_to(out)):sha(p) for p in (out/'manifest.json',out/'run.log',report,cosim,rtl)},physical_timing=False,board_result=False)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--expected-calls',type=int,default=75);p.add_argument('--out',required=True,type=Path);a=p.parse_args();r=audit(a.directory,a.expected_calls);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(0 if r['status']=='verified' else 2)
