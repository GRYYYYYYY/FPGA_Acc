"""Recover read-only review after producer helper-report census assertion; no recompile."""
import hashlib,json,re,xml.etree.ElementTree as E
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_split_start_HLS_screen_20261015'
def main():
 refs={}
 def sha(f):
  k=str(f)
  if k not in refs:refs[k]=hashlib.sha256(Path(f).read_bytes()).hexdigest()
  return refs[k]
 p=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='failed' and 'if flag:assert len(helper)==1' in m['traceback'];assert [x['returncode'] for x in m['steps']]==[0,0]
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 interfaces=[];rows=[];top='dieroute_net_commit_sharded_hbm'
 for flag in [0,1]:
  d=P/('flag'+str(flag));sol=d/'project/solution1';f=sol/'syn/report'/(top+'_csynth.xml');x=E.parse(f).getroot();constraint=sol/'.autopilot/db'/(top+'.constraint.tcl');b=re.search(r'set clock_constraint\s*\{(.*?)\}',constraint.read_text(),re.S);assert b
  period=Decimal(re.findall(r'\bperiod\s+([0-9.]+)',b[1])[0]);unc=Decimal(re.findall(r'\buncertainty\s+([0-9.]+)',b[1])[0]);assert (period,unc)==(Decimal('3.333'),Decimal('0.89991'));estimate=Decimal(x.findtext('.//EstimatedClockPeriod'));assert estimate<=period-unc
  rtl=sol/'syn/verilog'/(top+'.v');s=rtl.read_text();interfaces.append((sorted(re.sub(r'\s+',' ',v.strip()) for v in s.splitlines() if re.match(r'^(input|output|inout)\s',v)),dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',s,re.M))))
  log=d/'console.log';text=log.read_text();assert 'SHARDED_DIFFERENTIAL calls=75' in text and 'CSim done with 0 errors' in text
  helper=None
  if flag:
   h=sol/'syn/report/p_anonymous_namespace_phase_start_only_csynth.xml';hx=E.parse(h).getroot();assert hx.findtext('UserAssignments/TopModelName')=='p_anonymous_namespace_phase_start_only';helper=dict(estimate_ns=hx.findtext('.//EstimatedClockPeriod'),latency=E.tostring(hx.find('.//SummaryOfOverallLatency'),encoding='unicode'));sha(h)
  rows.append(dict(flag=flag,estimate_ns=str(estimate),effective_budget_ns=str(period-unc),reported_estimate_pass=True,resources={v.tag:int(v.text) for v in x.find('.//AreaEstimates/Resources')},helper=helper,all_loop_constraints_met='All loop constraints were NOT satisfied' not in text))
  for q in [f,constraint,rtl,log]:sha(q)
 assert interfaces[0]==interfaces[1] and (len(interfaces[0][0]),len(interfaces[0][1]))==(290,79)
 for q in [P/'manifest.json',P/'protocol.json',Path(__file__).resolve()]:sha(q)
 result=dict(status='both_start_phase_HLS_tools0_numeric_gate_and_ABI_verified_review_recovered',outcomes=rows,external_ports=290,bus_parameters=79,source_sha256=refs,adopted=False,research_complete=False,scope='Original producer failed only postcompile because broad helper glob also matched two subloops; no input/script or synthesis artifact modified, both tools0 retained. Exact main helper report selected by TopModelName. 75CSIMcalls per flag, effectiveclock andABI checked. NoRTL,fullnative,physical benefit or adoption; area increase retained. Protocol is authoritative commit description; copied producer generic description was not emitted to result.')
 with (P/'recovered_independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps([{k:v for k,v in row.items() if k!='helper'} for row in rows]))
if __name__=='__main__':main()
