"""Review paired start-validation HLS evidence without claiming physical closure."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as E
from decimal import Decimal
P=Path('work/native_start_validate_only_HLS_20261016')
def main():
 m=json.loads((P/'manifest.json').read_text());p=json.loads((P/'protocol.json').read_text())
 assert m['status']=='both_HLS_terminal_requires_independent_review'
 assert [s['returncode'] for s in m['steps']]==[0,0]
 refs={}
 def sha(f):
  refs[str(f)]=hashlib.sha256(Path(f).read_bytes()).hexdigest();return refs[str(f)]
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 rows=[];interfaces=[]
 for flag in [0,1]:
  d=P/f'flag{flag}';sol=d/'project/solution1';top='dieroute_net_commit_sharded_hbm'
  report=sol/'syn/report'/(top+'_csynth.xml');x=E.parse(report).getroot()
  constraint=sol/'.autopilot/db'/(top+'.constraint.tcl');c=constraint.read_text()
  b=re.search(r'set clock_constraint\s*\{(.*?)\}',c,re.S);assert b
  period=Decimal(re.findall(r'\bperiod\s+([0-9.]+)',b[1])[0]);uncertainty=Decimal(re.findall(r'\buncertainty\s+([0-9.]+)',b[1])[0]);assert period==Decimal('3.333')
  estimate=Decimal(x.findtext('.//EstimatedClockPeriod'))
  log=d/'console.log';t=log.read_text();assert 'SHARDED_DIFFERENTIAL calls=75' in t and 'CSim done with 0 errors' in t
  rtl=sol/'syn/verilog'/(top+'.v');s=rtl.read_text()
  interfaces.append((sorted(re.sub(r'\s+',' ',v.strip()) for v in s.splitlines() if re.match(r'^(input|output|inout)\s',v)),dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',s,re.M))))
  helpers=[]
  for f in sorted((sol/'syn/report').glob('*csynth.xml')):
   root=E.parse(f).getroot();name=root.findtext('UserAssignments/TopModelName','')
   if any(v in name for v in ['phase_start_only','phase_execute','insert']):
    helpers.append(dict(name=name,resources={v.tag:int(v.text) for v in root.find('.//AreaEstimates/Resources')}));sha(f)
  rows.append(dict(flag=flag,estimate_ns=str(estimate),effective_budget_ns=str(period-uncertainty),estimated_clock_pass=estimate<=period-uncertainty,resources={v.tag:int(v.text) for v in x.find('.//AreaEstimates/Resources')},helpers=helpers))
  for f in [report,constraint,log,rtl]:sha(f)
 assert interfaces[0]==interfaces[1]
 for f in [P/'manifest.json',P/'protocol.json',Path(__file__)]:sha(f)
 result=dict(status='paired_HLS_CSIM_ABI_and_resources_reviewed',outcomes=rows,resource_delta={k:rows[1]['resources'][k]-rows[0]['resources'][k] for k in rows[0]['resources']},source_sha256=refs,adopted=False,research_complete=False,board_result=False,scope='75 differential CSIM calls per arm. HLS estimates and helper report census only; no RTL co-simulation or physical routing success inferred.')
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
