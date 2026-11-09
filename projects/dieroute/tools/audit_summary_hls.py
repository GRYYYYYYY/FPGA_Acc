#!/usr/bin/env python3
"""Check the summary endpoint's frozen HLS/RTL evidence, never board timing."""
import argparse,hashlib,json,re,shutil,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();assert not a.output.exists()
 root=Path(__file__).resolve().parents[1];run=a.run.resolve();m=json.loads((run/'manifest.json').read_text());assert m['status']=='passed' and m['returncode']==0 and m['sources_unchanged']
 for rel,h in m['source_sha256'].items():assert sha(root/rel)==sha(run/'source'/rel)==h
 project=run/'project';report=project/'u280/syn/report/dieroute_summary_hbm_csynth.xml';xml=ET.parse(report).getroot()
 assert xml.findtext('ReportVersion/Version')=='2022.2' and xml.findtext('UserAssignments/Part')==m['part']
 assert xml.findtext('UserAssignments/TopModelName')=='dieroute_summary_hbm'
 target=float(xml.findtext('UserAssignments/TargetClockPeriod'));uncertainty=float(xml.findtext('UserAssignments/ClockUncertainty'));estimate=float(xml.findtext('PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod'))
 assert target==4 and estimate+uncertainty<=target+1e-9
 resources={r.tag:int(r.text) for r in xml.find('AreaEstimates/Resources')}
 cosim=project/'u280/sim/report/dieroute_summary_hbm_cosim.rpt';line=next(x for x in cosim.read_text().splitlines() if re.search(r'\|\s*Verilog\s*\|',x));values=[x.strip() for x in line.split('|')[1:-1]];assert values[1]=='Pass';cycles=list(map(int,values[2:]));assert len(cycles)==7
 log=(run/'run.log').read_text();assert 'CSim done with 0 errors' in log and 'C/RTL co-simulation finished: PASS' in log and 'HLS 200-871' not in log
 simulations=re.findall(r'RTL Simulation : (\d+) / (\d+)',log);assert simulations and simulations[-1]==('15','15')
 shared=m.get('shared_traffic',False);assert type(shared) is bool
 if shared:assert 'DIEROUTE_SUMMARY_SHARED_TRAFFIC=1' in log
 xo=project/'dieroute_summary_hbm.xo'
 with zipfile.ZipFile(xo) as z:kernel=ET.fromstring(z.read('dieroute_summary_hbm/kernel.xml')).find('kernel')
 expected={'M_AXI_INGRESS':512,'M_AXI_DIRECTORY':64,'M_AXI_OWNER_STATE':512,'M_AXI_SHADOW_STATE':512,'M_AXI_EGRESS':512}
 if shared:del expected['M_AXI_EGRESS']
 ports={p.attrib['name']:int(p.attrib['dataWidth']) for p in kernel.find('ports') if p.attrib['mode']=='master'};assert ports==expected
 args=list(kernel.find('args'));names=['commands','topology','owners','shadows','responses','completion','slots','lanes','die','dies','session','command_capacity','response_capacity','command_read','command_write','response_read','response_write','max_steps']
 assert [x.attrib['name'] for x in args]==names and [int(x.attrib['id']) for x in args]==list(range(18))
 assert [int(x.attrib['size'],0) for x in args]==[8]*6+[4]*4+[8,4,4,8,8,8,8,4]
 reply='M_AXI_INGRESS' if shared else 'M_AXI_EGRESS'
 assert [x.attrib['port'] for x in args[:6]]==['M_AXI_INGRESS','M_AXI_DIRECTORY','M_AXI_OWNER_STATE','M_AXI_SHADOW_STATE',reply,reply]
 rtl=project/'u280/syn/verilog/dieroute_summary_hbm.v';text=rtl.read_text()
 for port,width in expected.items():assert re.search(r'C_'+port+r'_DATA_WIDTH\s*=\s*'+str(width)+r'\s*;',text)
 artifacts=[run/'manifest.json',run/'run.log',report,report.with_suffix('.rpt'),cosim,xo,rtl]
 result=dict(schema='dieroute.summary_hbm_hls_audit.v1',passed=True,source_matches_current=True,inputs={str(p):sha(p) for p in artifacts},clock_target_ns=target,clock_uncertainty_ns=uncertainty,hls_estimated_period_ns=estimate,hls_effective_budget_met=True,estimated_resources=resources,axi_data_widths=ports,rtl_test_launches=15,cosim_cycles=dict(latency_min=cycles[0],latency_avg=cycles[1],latency_max=cycles[2],interval_min=cycles[3],interval_avg=cycles[4],interval_max=cycles[5],total=cycles[6]),warnings=[x for x in log.splitlines() if x.startswith('WARNING:')],scope='Component synthesis estimates and directed RTL testbench; no platform implementation, HBM latency or physical timing result',board_result=False)
 result['shared_traffic']=shared
 a.output.mkdir();shutil.copy2(__file__,a.output/'audit_summary_hls.py');result['auditor_sha256']=sha(__file__);(a.output/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
