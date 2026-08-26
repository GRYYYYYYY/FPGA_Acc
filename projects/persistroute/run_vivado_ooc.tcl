set script_dir [file dirname [file normalize [info script]]]
set build_dir [file join $script_dir build]
set part_name {xcu280-fsvh2892-2L-e}

proc synth_kernel {script_dir build_dir part_name top solution_dir} {
 set rtl_dir [file join $build_dir $solution_dir syn verilog]
 set out_dir [file join $build_dir vivado_ooc $top]
 if {![file isdirectory $rtl_dir]} {
  error "HLS RTL directory not found: $rtl_dir; run run_hls.sh first"
 }
 file mkdir $out_dir
 create_project -force ${top}_ooc [file join $out_dir project] -part $part_name
 read_verilog [glob -nocomplain [file join $rtl_dir *.v]]
 set vhdl_files [glob -nocomplain [file join $rtl_dir *.vhd]]
 if {[llength $vhdl_files] > 0} {read_vhdl $vhdl_files}
 synth_design -mode out_of_context -top $top -part $part_name
 create_clock -name ap_clk -period 4.000 [get_ports ap_clk]
 set_param general.maxThreads 6
 opt_design
 report_timing_summary -delay_type max -max_paths 10 -file [file join $out_dir timing_summary.rpt]
 report_utilization -file [file join $out_dir utilization.rpt]
 report_clock_utilization -file [file join $out_dir clock_utilization.rpt]
 report_drc -file [file join $out_dir drc.rpt]
 write_checkpoint -force [file join $out_dir ${top}_ooc.dcp]
 close_project
}

synth_kernel $script_dir $build_dir $part_name search_hbm_kernel \
 [file join search_hbm_project search_hbm_u280]
synth_kernel $script_dir $build_dir $part_name commit_hbm_kernel \
 [file join commit_hbm_project commit_hbm_u280]
exit
