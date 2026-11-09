# Run from a frozen source directory containing include/, src/, tb/.
set d [file normalize [pwd]]
if {![info exists ::env(DIEROUTE_SUMMARY_HLS_OUT)]} {error "DIEROUTE_SUMMARY_HLS_OUT required"}
set out [file normalize $::env(DIEROUTE_SUMMARY_HLS_OUT)]
set shared 0
if {[info exists ::env(DIEROUTE_SUMMARY_SHARED_TRAFFIC)]} {set shared $::env(DIEROUTE_SUMMARY_SHARED_TRAFFIC)}
if {$shared ni {0 1}} {error "DIEROUTE_SUMMARY_SHARED_TRAFFIC must be 0 or 1"}
puts "DIEROUTE_SUMMARY_SHARED_TRAFFIC=$shared"
set flags "-std=c++14 -I[file join $d include] -DDIEROUTE_SUMMARY_SHARED_TRAFFIC=$shared"
if {[file exists $out]} {error "refuse to overwrite HLS project"}
cd [file dirname $out]
open_project [file tail $out]
set_top dieroute_summary_hbm
add_files [file join $d src summary_hbm.cpp] -cflags $flags
add_files -tb [file join $d tb summary_hbm_tb.cpp] -cflags $flags
open_solution u280 -flow_target vitis
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4.0
csim_design
csynth_design
cosim_design -rtl verilog
export_design -format xo -output [file join $out dieroute_summary_hbm.xo]
exit
