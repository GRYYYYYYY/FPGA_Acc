"""Review successful image generation separately from requested-clock signoff."""
from pathlib import Path
import hashlib,json,re,collections
R=Path(__file__).resolve().parents[1];B=R/'work/native_commit_const_zero_variant_20261015';P=R/'work/const_zero_postlink_readonly_reports_20261015';C=R/'work/const_zero_final_clock_metadata_20261015';cache={}
def sha(f):
 f=str(Path(f).resolve())
 if f not in cache:
  h=hashlib.sha256()
  with Path(f).open('rb') as v:
   for b in iter(lambda:v.read(1048576),b''):h.update(b)
  cache[f]=h.hexdigest()
 return cache[f]
def load(f):return json.loads(Path(f).read_text())
def timing(tokens):
 assert len(tokens)==12
 names=['wns_ns','tns_ns','setup_failing','setup_total','whs_ns','ths_ns','hold_failing','hold_total','wpws_ns','tpws_ns','pulse_failing','pulse_total']
 return {key:(int(value) if 'failing' in key or 'total' in key else float(value)) for key,value in zip(names,tokens)}
def main():
 link=load(B/'link_manifest.json');post=load(P/'manifest.json');assert link['status']=='linked_requires_independent_routed_signoff' and link['returncode']==0
 assert post['status']=='readonly_reports_complete_signoff_interpretation_required' and post['returncode']==0 and post['checkpoint_unchanged']
 assert sha(B/'joint.xclbin')==link['xclbin_sha256']==post['xclbin_sha256']
 named=B/'link_temp/link/vivado/vpl/prj/prj.runs/impl_1/level0_wrapper_routed.dcp';assert sha(named)==link['retained_checkpoints'][str(named)]==post['checkpoint_sha256']
 archive=Path(post['command'][post['command'].index('-tclargs')+1]);assert sha(archive)==post['checkpoint_sha256']
 for f,h in post['report_sha256'].items():assert sha(f)==h,f
 report=(P/'reports/timing_summary.rpt').read_text();block=report.split('Design Timing Summary',1)[1];summary=None
 for line in block.splitlines():
  tokens=line.split()
  if len(tokens)==12 and all(tokens[i].isdigit() for i in [2,3,6,7,10,11]):summary=timing(tokens);break
 assert summary and summary['wns_ns']==-2.413 and summary['tns_ns']==-38255.922 and summary['setup_failing']==60945
 kernel=None
 for line in report.splitlines():
  tokens=line.split()
  if len(tokens)==13 and tokens[0]=='clk_kernel_00_unbuffered_net':kernel=timing(tokens[1:]);break
 assert kernel and kernel['setup_failing']==60479
 metrics=dict(line.split('\t',1) for line in (P/'reports/metrics.tsv').read_text().splitlines());assert float(metrics['setup_worst_slack_ns'])==summary['wns_ns']
 assert len(post['kernel_clocks'])==3 and all(float(v['period_ns'])==3.333 and v['clock']=='clk_kernel_00_unbuffered_net' for v in post['kernel_clocks'])
 clocks=load(C/'clock_freq_topology.json')['clock_freq_topology']['m_clock_freq'];freq={v['m_name']:int(v['m_freq_Mhz']) for v in clocks};assert freq=={'hbm_aclk':403,'KERNEL_CLK':500,'DATA_CLK':174}
 log=(B/'link_logs/link/vivado.log').read_text();assert "frequency is being automatically changed to 174.0 MHz" in log and 'targeting 300.000000 MHz' in log
 drc=(P/'reports/drc.rpt').read_text();rules=re.findall(r'^\|\s*([A-Z][A-Z0-9-]+)\s*\|\s*(Error|Critical Warning|Warning|Advisory)\s*\|[^\n]*?\|\s*(\d+)\s*\|',drc,re.M);severity=collections.Counter()
 for _,kind,count in rules:severity[kind]+=int(count)
 assert sum(severity.values())==321 and severity['Error']==severity['Critical Warning']==0
 route=(P/'reports/route_status.rpt').read_text();assert re.search(r'nets with routing errors[^\n]*:\s*0\s*:',route)
 parent=R/'work/native_snapshot_sharded_independent_report_audit_20261015/audit.json';old=load(parent);assert old['design_timing_summary']['wns_ns']==-2.014 and old['clock_metadata']['data_clock_topology_mhz']==187
 for f in [B/'link_manifest.json',B/'link.stdout',B/'link_logs/link/vivado.log',P/'manifest.json',C/'clock_freq_topology.json',C/'dump.stdout',C/'dump.stderr',parent,Path(__file__).resolve()]:sha(f)
 result=dict(status='const_zero_link_succeeded_requested300MHz_signoff_failed_no_adoption',requested_kernel_mhz=300,final_clock_topology_mhz=freq,design_timing_summary=summary,kernel_timing_summary=kernel,worst_setup_startpoint=metrics['setup_startpoint'],worst_setup_endpoint=metrics['setup_endpoint'],drc_severity_counts=dict(severity),route_complete=True,bus_skew=post['bus_skew'],parent_observation={'wns_ns':-2.014,'DATA_CLK_metadata_mhz':187},observed_wns_delta_ns=round(summary['wns_ns']+2.014,3),source_sha256=cache,scope='Exact completed-link image and named retained routed checkpoint hashes verified; report and final clock metadata cross-check. Checkpoint300MHz setup fails; tool automatically scales DATA clock174/systemHBM403. Relative parent observed WNS/metadata are worse in one implementation each, not causal or statistical attribution. No final-bitstream-to-checkpoint correspondence, adjusted-clock signoff, Fmax, board, adoption or research completion claim.',adopted=False,board_result=False,research_complete=False)
 with (C/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','bus_skew']}))
if __name__=='__main__':main()
