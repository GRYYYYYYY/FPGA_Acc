set d [file normalize [pwd]]
if {![info exists ::env(DIEROUTE_NET_COMMIT_HLS_OUT)]} {error "DIEROUTE_NET_COMMIT_HLS_OUT required"}
set out [file normalize $::env(DIEROUTE_NET_COMMIT_HLS_OUT)]
if {[file exists $out]} {error "refuse to overwrite HLS project"}
cd [file dirname $out]
open_project [file tail $out]
set_top dieroute_net_commit_hbm
add_files [file join $d src net_commit_hbm.cpp] -cflags "-std=c++14 -I[file join $d include]"
foreach test {net_commit_hbm_tb.cpp net_commit_adversarial_tb.cpp} {
 add_files -tb [file join $d tb $test] -cflags "-std=c++14 -DDIEROUTE_COMMIT_COMBINED_TB -I[file join $d include] -I[file join $d tb]"
}
open_solution u280 -flow_target vitis
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4.0
config_compile -pipeline_loops 0
csim_design
csynth_design
cosim_design -rtl verilog
export_design -format xo -output [file join $out dieroute_net_commit_hbm.xo]
exit
