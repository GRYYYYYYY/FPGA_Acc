"""Review ripup predecessor helper experiment, preserving cycle and timing limitations."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1]
P=R/'work/ripup_predecessor_helper_HLS_20261018'
B=R/'work/publish_record_serial_HLS_20261018'
def main():
 refs={}
 def sha(p):
  p=Path(p);v=hashlib.sha256(p.read_bytes()).hexdigest();refs[str(p.resolve())]=v;return v
 for name in ['protocol.json','cosim_protocol.json']:
  for f,h in json.loads((P/name).read_text())['source_sha256'].items():assert sha(f)==h,f
 m=json.loads((P/'cosim_manifest.json').read_text());assert m['status']=='cosim_terminal_requires_review' and m['returncode']==0,m
 log=(P/'cosim.log').read_text();assert 'C/RTL co-simulation finished: PASS' in log
 progress=re.findall(r'RTL Simulation : (\d+) / (\d+)',log);assert progress and progress[-1]==('75','75')
 assert {p.name for p in (P/'source').iterdir()}=={p.name for p in (B/'source').iterdir()}
 changed=[p.name for p in (P/'source').iterdir() if sha(p)!=sha(B/'source'/p.name)]
 assert changed==['net_commit_sharded_hbm.cpp'],changed
 top='dieroute_net_commit_sharded_hbm';sol=P/'project/solution1'
 def abi(p):
  t=p.read_text();sha(p)
  return sorted(re.sub(r'\s+',' ',v.strip()) for v in t.splitlines() if re.match(r'^(input|output|inout)\s',v)),dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',t,re.M))
 a=abi(sol/'syn/verilog'/f'{top}.v');b=abi(B/'project/solution1/syn/verilog'/f'{top}.v');assert a[0] and a==b
 def cycles(p):
  t=p.read_text();sha(p)
  rows=[l for l in t.splitlines() if re.match(r'\|\s*Verilog\s*\|\s*Pass\s*\|',l)]
  assert len(rows)==1;cells=[c.strip() for c in rows[0].split('|')][1:-1];assert len(cells)==9,cells
  return int(cells[-1]),t
 count,raw=cycles(sol/'sim/report'/f'{top}_cosim.rpt');base,_=cycles(B/'project/solution1/sim/report'/f'{top}_cosim.rpt')
 xfile=sol/'syn/report'/f'{top}_csynth.xml';x=E.parse(xfile).getroot();assert x.findtext('UserAssignments/Part')=='xcu280-fsvh2892-2L-e'
 period=float(x.findtext('.//EstimatedClockPeriod'));assert period==2.433
 for p in [P/'cosim_manifest.json',P/'cosim.log',P/'independent_HLS_audit.json',xfile,Path(__file__)]:sha(p)
 result={'status':'ripup_predecessor_helper_75_call_Verilog_ABI_and_cycle_cost_reviewed','rtl_calls':75,'external_ABI_matches_parent':True,'candidate_cycles':count,'parent_cycles':base,'cycle_delta_percent':100*(count/base-1),'HLS_estimated_period_ns':period,'resources':{e.tag:int(e.text) for e in x.find('.//AreaEstimates/Resources')},'cosim_report':raw,'source_sha256':refs,'scope':'75 original normal/adversarial fixture calls only. Total simulation cycle cost is not representative workload throughput; HLS period is not routed timing. Full timing/DRC/route signoff and physical-board performance remain unproven. No adoption.','adopted':False,'board_result':False,'research_complete':False}
 with (P/'independent_RTL_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','cosim_report']}))
if __name__=='__main__':main()
