"""Review the isolated publication helper experiment after its original run ends."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
P=R/'work/publish_record_split_RTL_20261018'
B=R/'work/proposal_generation_split_RTL_20261018'
def main():
 refs={}
 def bind(p):
  p=Path(p);v=hashlib.sha256(p.read_bytes()).hexdigest();refs[str(p.resolve())]=v;return v
 protocol=json.loads((P/'protocol.json').read_text())
 for p,h in protocol['source_sha256'].items():assert bind(p)==h,p
 manifest=json.loads((P/'manifest.json').read_text())
 assert manifest['status']=='rtl_terminal_requires_review' and manifest['returncode']==0,manifest
 changed=[]
 assert {p.name for p in (P/'source').iterdir()}=={p.name for p in (B/'source').iterdir()}
 for p in (P/'source').iterdir():
  if bind(p)!=bind(B/'source'/p.name):changed.append(p.name)
 assert changed==['net_commit_sharded_hbm.cpp'],changed
 log=(P/'run.log').read_text()
 assert 'C/RTL co-simulation finished: PASS' in log
 assert 'CSim done with 0 errors' in log
 assert 'SHARDED_DIFFERENTIAL calls=75 isolated_owner_banks=3' in log
 progress=re.findall(r'RTL Simulation : (\d+) / (\d+)',log)
 assert progress and progress[-1]==('75','75'),progress[-3:]
 top='dieroute_net_commit_sharded_hbm'
 sol=P/'project/solution1'
 report=sol/'sim/report'/f'{top}_cosim.rpt'
 text=report.read_text();assert re.search(r'\|\s*Verilog\s*\|\s*Pass\s*\|',text)
 def abi(p):
  t=p.read_text();bind(p)
  return sorted(re.sub(r'\s+',' ',v.strip()) for v in t.splitlines() if re.match(r'^(input|output|inout)\s',v)),dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',t,re.M))
 a=abi(sol/'syn/verilog'/f'{top}.v');b=abi(B/'project/solution1/syn/verilog'/f'{top}.v')
 assert a[0] and a==b,'external RTL ABI drift'
 xml=sol/'syn/report'/f'{top}_csynth.xml';x=ET.parse(xml).getroot()
 assert x.findtext('UserAssignments/Part')=='xcu280-fsvh2892-2L-e'
 period=float(x.findtext('UserAssignments/TargetClockPeriod'));assert abs(period-3.333)<.01
 helpers=list((sol/'syn/verilog').glob('*publish_record*.v'));assert helpers,'helper not retained'
 for p in helpers:bind(p)
 for p in [P/'protocol.json',P/'manifest.json',P/'run.log',P/'run.tcl',P/'source.diff',report,xml,Path(__file__),B/'independent_audit.json']:bind(p)
 result={'status':'publication_record_helper_75_call_C_Verilog_and_external_ABI_reviewed','rtl_calls':75,'external_ABI_matches_parent':True,'only_changed_source':changed,'HLS':{'estimated_period_ns':float(x.findtext('.//EstimatedClockPeriod')),'resources':{e.tag:int(e.text) for e in x.find('.//AreaEstimates/Resources')}},'cosim_report':text,'parent_cycles':json.loads((B/'independent_audit.json').read_text())['candidate_cycles'],'source_sha256':refs,'scope':'Bounded normal/adversarial test equivalence and unchanged RTL external declarations. HLS estimates are not routed timing or board performance. Full destination semantics and physical effects still require engineering review.','adopted':False,'board_result':False,'research_complete':False}
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','cosim_report']}))
if __name__=='__main__':main()
