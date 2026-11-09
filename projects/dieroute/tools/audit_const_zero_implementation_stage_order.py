"""Archive generated planned implementation order without claiming runtime/finality."""
import hashlib,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'work/const_zero_implementation_stage_order_20261015'
def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
def main():
 candidate=ROOT/'work/native_commit_const_zero_variant_20261015';vpl=candidate/'link_temp/link/vivado/vpl'
 files={'implementation.tcl':vpl/'prj/prj.runs/impl_1/level0_wrapper.tcl','route_post_hook.tcl':vpl/'scripts/impl_1/_full_route_post.tcl','vpl_post_route.tcl':vpl/'scripts/_vpl_post_route.tcl','platform_postroute.tcl':vpl/'.local/hw_platform/tcl_hooks/postroute.tcl','write_bitstream_pre_hook.tcl':vpl/'scripts/impl_1/_full_write_bitstream_pre.tcl','vpl_pre_write_bit.tcl':vpl/'scripts/_vpl_pre_write_bit_pdi.tcl','ocl_util.tcl':Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis/2022.2/scripts/ocl/ocl_util.tcl')}
 receipts=[]
 for name,source in files.items():
  raw=source.read_bytes();archive=P/name
  if not archive.exists():shutil.copyfile(source,archive)
  assert archive.read_bytes()==raw==source.read_bytes(),source
  receipts.append(dict(source=str(source),archive=str(archive),sha256=sha(source),bytes=len(raw)))
 s=(P/'implementation.tcl').read_text();lines=s.splitlines()
 patterns=[('route_design',r'^  route_design\s*$'),('route_post_hook',r'^    source .*/_full_route_post\.tcl$'),('routed_checkpoint',r'^  write_checkpoint -force level0_wrapper_routed\.dcp$'),('platform_wrapper_property',r'^  set_property HD\.PLATFORM_WRAPPER 1 '),('bitstream_pre_hook',r'^    source .*/_full_write_bitstream_pre\.tcl$'),('partial_bitstream',r'^  write_bitstream -force -cell level0_i/ulp level0_i_ulp_my_rm_partial\.bit\s*$')]
 order=[]
 for name,pattern in patterns:
  match=[i+1 for i,line in enumerate(lines) if re.search(pattern,line)];assert len(match)==1,(name,match);order.append(dict(step=name,line=match[0]))
 assert [r['line'] for r in order]==sorted(r['line'] for r in order)
 pre=(P/'vpl_pre_write_bit.tcl').read_text();assert 'enable_auto_freq_scale true' in pre and 'freq 300.000000' in pre and 'freq_orig 450 freq 450' in pre
 platform=(P/'platform_postroute.tcl').read_text();assert platform.strip()=='report_power'
 assert not re.search(r'^\s*post_route_phys_opt_design\s*$',s,re.M)
 util=(P/'ocl_util.tcl').read_text();a=util.index('  proc report_timing_and_scale_freq ');b=util.index('\n  proc ',a+8);body=util[a:b]
 assert 'if { ![file exists $routed_timing_dcp] }' in body and 'if { $is_timing_failure }' in body
 excerpt=P/'report_timing_and_scale_freq.excerpt.tcl';excerpt.write_text(body+'\n')
 report=dict(status='generated_implementation_checkpoint_and_bitstream_phase_order_archived',candidate=str(candidate),ordered_steps=order,post_checkpoint_property='HD.PLATFORM_WRAPPER=1',timing_pre_hook=dict(auto_frequency_scaling=True,kernel_requested_mhz=300,system_scaling_input_mhz=450),platform_postroute_hook=dict(command='report_power',bytes=len(platform.encode()),trailing_newline=platform.endswith('\n')),explicit_post_route_physopt_step_in_this_generated_run=False,conditional_timing_checkpoint='Vendor helper emits dr_routed_timing.dcp on hold/timing-failure paths; it is not guaranteed on successful scaling.',receipts=receipts,source_sha256={str(q):sha(q) for q in [*(P/name for name in files),excerpt,P/'attempt1.json',Path(__file__).resolve()]},scope='Staticgeneratedplannedorderonly;originalimplementationstillrunning. NamedroutedDCPprecedeslaterproperty/clockprocessing. Notprooflateroperationsleavephysical/configurationstateunchanged,allphasesexecuted,finalbitstreamcorrespondence,300MHzclosureorphysicalboardoperation. Firstincorrectempty-hookassertionretained;12bytepowerreportcommandnowexplicit.',board_result=False,research_complete=False)
 with (P/'audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['receipts','source_sha256']}))
if __name__=='__main__':main()
