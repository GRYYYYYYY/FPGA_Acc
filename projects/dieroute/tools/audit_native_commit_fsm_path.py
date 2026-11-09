"""Extract checkpoint-specific commit timing and generated FSM facts."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_commit_fsm_path_diagnosis_20261015'
def main():
 report=R/'work/const_zero_postlink_readonly_reports_20261015/reports/timing_summary.rpt'
 rtl=R/'work/native_commit_const_zero_variant_20261015/link_temp/link/int/xo/ip_repo/xilinx_com_hls_dieroute_net_commit_sharded_hbm_1_0/hdl/verilog/dieroute_net_commit_sharded_hbm.v'
 text=report.read_text();v=rtl.read_text();m=re.search(r'Slack \(VIOLATED\)\s*:\s*(-[\d.]+)ns.*?Source:\s*(\S+).*?Destination:\s*(\S+).*?Data Path Delay:\s*([\d.]+)ns\s*\(logic ([\d.]+)ns.*?route ([\d.]+)ns \(([\d.]+)%\)\).*?Logic Levels:\s*(\d+)(.*?)(?=Slack \(|Min Delay Paths|$)',text,re.S);assert m
 slack,source,dest,total,logic,route,percentage,levels,detail=m.groups();assert source.endswith('ap_CS_fsm_reg[2481]/C') and float(slack)==-2.413
 width=int(re.search(r'fsm_encoding = "none" \*\) reg\s*\[(\d+):0\] ap_CS_fsm;',v).group(1))+1
 states=re.findall(r'parameter\s+ap_ST_fsm_state(\d+) = (\d+)\'d(\d+);',v)
 assert len(states)==width==2496
 for i,w,n in states:assert int(w)==width and int(n)==1<<(int(i)-1)
 assert 'ap_CS_fsm_state2482' in detail and '/grp_p_anonymous_namespace_store_fu_2735/' in detail
 helptext=re.sub(r'\x1b\[[0-9;]*m','',(P/'config_rtl_help.log').read_text());assert 'config_rtl [OPTIONS]' in helptext
 facts=dict(status='named_routed_checkpoint_commit_FSM_store_to_AXI_path_characterized',fsm=dict(width=width,states=len(states),all_state_parameters_one_hot=True,synthesis_attribute='fsm_encoding=none',critical_state=2482),critical_path=dict(slack_ns=float(slack),source=source,destination=dest,data_delay_ns=float(total),logic_delay_ns=float(logic),route_delay_ns=float(route),route_percent=float(percentage),logic_levels=int(levels),reported_path_net_fanouts_including_clock=[int(n) for n in re.findall(r'net \(fo=(\d+), routed\)',detail)]),local_config_rtl_help_has_fsm_encoding_option=bool(re.search(r'-[a-z_]*fsm|-[a-z_]*encoding',helptext)),scope='One named pre-final-frequency routed checkpoint, rejected const-zero variant. Generated one-hot state representation and store call control belong to critical path; causality and benefit of changing encoding are unproven. No final adjusted-clock signoff or board result.',next_step='Inspect store helper scalar/control and AXI handshakes before choosing isolated function-boundary or pipeline change; no unsupported config_rtl encoding command or production edit.',board_result=False,research_complete=False)
 files=[report,rtl,P/'config_rtl_help.log',P/'help.tcl',Path(__file__).resolve(),R/'work/const_zero_final_clock_metadata_20261015/independent_audit.json']
 facts['source_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
 with (P/'independent_audit.json').open('x') as f:json.dump(facts,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in facts.items() if k!='source_sha256'}))
if __name__=='__main__':main()
