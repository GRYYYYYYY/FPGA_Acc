"""Review compact42path/256reads diagnostic; never substitute for full native XRT."""
import hashlib,json,re,xml.etree.ElementTree as E
from pathlib import Path
from zipfile import ZipFile
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_42path_256reads_RTL_diagnostic_v2_20261015'
def main():
 refs={}
 def sha(f):
  h=hashlib.sha256(Path(f).read_bytes()).hexdigest();refs[str(f)]=h;return h
 for name in ['protocol.json','hls_protocol.json','launch_protocol.json']:
  for f,h in json.loads((P/name).read_text())['source_sha256'].items():assert sha(f)==h,f
 m=json.loads((P/'manifest.json').read_text());assert m['status']=='HLS_terminal_requires_independent_review' and m['returncode']==0,m
 log=(P/'run.log').read_text();assert 'CSim done with 0 errors' in log and 'C/RTL co-simulation finished: PASS' in log
 assert log.count('LARGE_COMMIT_PROTOCOL calls=45 readset=256 path_nodes=42 owners=3 revision=2')>=2 and log.count('SHARDED_DIFFERENTIAL calls=45 isolated_owner_banks=3')>=2
 progress=[tuple(map(int,p)) for p in re.findall(r'RTL Simulation : (\d+) / (\d+)',log)];assert progress and progress[-1]==(45,45)
 sol=P/'project/solution1';top='dieroute_net_commit_sharded_hbm';xml=sol/'syn/report'/(top+'_csynth.xml');cosim=sol/'sim/report'/(top+'_cosim.rpt');assert re.search(r'\|\s*Verilog\s*\|\s*Pass\s*\|',cosim.read_text())
 x=E.parse(xml).getroot();assert x.findtext('UserAssignments/Part')=='xcu280-fsvh2892-2L-e' and x.findtext('UserAssignments/TargetClockPeriod')=='3.33'
 parent=R/'work/net_commit_sharded_hls_v3_20261014/project/solution1/syn/verilog';candidate=sol/'syn/verilog'
 old={p.name:p for p in parent.glob('*.v')};new={p.name:p for p in candidate.glob('*.v')};assert old and new
 shared=sorted(old.keys()&new.keys());mismatched=[name for name in shared if sha(old[name])!=sha(new[name])]
 with ZipFile(R/'work/native_higher_g_hw_emu_link_20261015/commit.xo') as z:
  packaged={Path(n).name:z.read(n) for n in z.namelist() if '/hdl/verilog/' in n and n.endswith('.v')}
  xo_common=sorted(packaged.keys()&new.keys());xo_mismatched=[name for name in xo_common if hashlib.sha256(packaged[name]).hexdigest()!=sha(new[name])]
 def abi(text):return sorted(re.sub(r'\s+',' ',line.strip()) for line in text.splitlines() if re.match(r'^(input|output|inout)\s',line)),dict(re.findall(r'^parameter\s+(C_[MS]_AXI_[A-Z0-9_]+)\s*=\s*([^;]+);',text,re.M))
 a=abi(new[top+'.v'].read_text());assert a==abi(old[top+'.v'].read_text())
 for f in [xml,cosim,P/'protocol.json',P/'hls_protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'run.log',Path(__file__).resolve()]:sha(f)
 result=dict(status='compact42path256reads45_Verilog_differential_calls_pass',RTL_calls=45,readset=256,path_nodes=42,owners=3,matching_external_port_declarations=len(a[0]),matching_bus_parameters=len(a[1]),parent_RTL_comparison=dict(shared_files=len(shared),different_files=mismatched,parent_only=sorted(old.keys()-new.keys()),candidate_only=sorted(new.keys()-old.keys()),all_files_byte_identical=old.keys()==new.keys() and not mismatched),actual_XRT_XO_RTL_comparison=dict(shared_files=len(xo_common),different_files=xo_mismatched,packaged_only=sorted(packaged.keys()-new.keys()),candidate_only=sorted(new.keys()-packaged.keys()),all_files_byte_identical=packaged.keys()==new.keys() and not xo_mismatched),estimated_period_ns=float(x.findtext('.//EstimatedClockPeriod')),resources={v.tag:int(v.text) for v in x.find('.//AreaEstimates/Resources')},source_sha256=refs,scope='Auxiliary compact300node fixture with traffic counts42path/256reads and three owner ports. Originalkernelbody except test-marshalling depth pragmas,45 guarded flat/sharded calls, structural tree/owner/revision/query-purity checks. Full HDL byte comparisons are recorded literally, not assumed; no fullnativegraph or sharedHBM XRT wait resolution, physical timing/performance or adoption claim.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
