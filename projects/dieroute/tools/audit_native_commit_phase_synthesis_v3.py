"""Check terminal six-phase synthesis, interfaces and per-module timing."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_phase_synthesis_20261015'
def main():
 refs={}
 def sha(f):
  h=hashlib.sha256(Path(f).read_bytes()).hexdigest();refs[str(f)]=h;return h
 for name in ['protocol.json','launch_protocol.json']:
  for f,h in json.loads((P/name).read_text())['source_sha256'].items():assert sha(f)==h,f
 m=json.loads((P/'manifest.json').read_text());assert m['status']=='HLS_exited_requires_independent_review' and m['returncode']==0,m
 log=(P/'run.log').read_text();assert 'CSim done with 0 errors' in log and 'SHARDED_DIFFERENTIAL calls=75 isolated_owner_banks=3' in log
 sol=P/'project/solution1/syn';top='dieroute_net_commit_sharded_hbm';xml=sol/'report'/(top+'_csynth.xml');x=E.parse(xml).getroot();assert x.findtext('UserAssignments/TargetClockPeriod')=='3.33' and x.findtext('UserAssignments/Part')=='xcu280-fsvh2892-2L-e'
 def abi(s):return sorted(re.sub(r'\s+',' ',v.strip()) for v in s.splitlines() if re.match(r'^(input|output|inout)\s',v)),dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',s,re.M))
 rtl=sol/'verilog'/(top+'.v');parent=R/'work/net_commit_sharded_hls_v3_20261014/project/solution1/syn/verilog'/(top+'.v');a=abi(rtl.read_text());old=abi(parent.read_text());assert a[0] and old[0]
 reports=[sol/'report'/('p_anonymous_namespace_phase_'+name+'_csynth.xml') for name in ['validate_reads','query','start','proposal','ripup','negotiate']];assert all(f.exists() for f in reports)
 rows=[]
 for f in [xml]+reports:
  z=E.parse(f).getroot();name=z.findtext('UserAssignments/TopModelName');v=sol/'verilog'/((name if name==top else top+'_'+name)+'.v');text=v.read_text();width=re.search(r'fsm_encoding = "none" \*\) reg\s*\[(\d+):0\] ap_CS_fsm;',text)
  rows.append(dict(module=name,estimated_period_ns=float(z.findtext('.//EstimatedClockPeriod')),resources={e.tag:int(e.text) for e in z.find('.//AreaEstimates/Resources')},fsm_bits=int(width[1])+1 if width else None));sha(f);sha(v)
 warnings=[dict(estimate_ns=float(a),requested_ns=float(b),uncertainty_ns=float(c),effective_budget_ns=float(d)) for a,b,c,d in re.findall(r'Estimated clock period \(([\d.]+)ns\) exceeds the target \(target clock period: ([\d.]+)ns, clock uncertainty: ([\d.]+)ns, effective delay budget: ([\d.]+)ns\)',log)]
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'run.log',parent,Path(__file__).resolve()]:sha(f)
 result=dict(status='six_phase_Csim75_and_synthesis_independently_reviewed_RTL_unproved',modules=rows,external_ABI_matches_parent=a==old,external_port_declarations=len(a[0]),bus_parameters=len(a[1]),timing_warnings=warnings,effective_timing_gate_pass=not warnings,source_sha256=refs,scope='Same3.333ns Csim/synthesis, six operation-phase helpers. Per-module area cannot be summed as placed utilization; hierarchy and timing are HLS only. RTL and physical signoff unproved. No adoption.',adopted=False,board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
