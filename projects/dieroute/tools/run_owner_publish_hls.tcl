# Run from a frozen source directory containing include/, src/, tb/.
set d [file normalize [pwd]]
if {![info exists ::env(DIEROUTE_OWNER_PUBLISH_HLS_OUT)]} {error "DIEROUTE_OWNER_PUBLISH_HLS_OUT required"}
set out [file normalize $::env(DIEROUTE_OWNER_PUBLISH_HLS_OUT)]
if {[file exists $out]} {error "refuse to overwrite HLS project"}
cd [file dirname $out]
open_project [file tail $out]
set_top dieroute_owner_publish_hbm
add_files [file join $d src owner_publish_hbm.cpp] -cflags "-std=c++14 -I[file join $d include]"
add_files -tb [file join $d tb owner_publish_hbm_tb.cpp] -cflags "-std=c++14 -I[file join $d include]"
open_solution u280 -flow_target vitis
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4.0
csim_design
csynth_design
cosim_design -rtl verilog
export_design -format xo -output [file join $out dieroute_owner_publish_hbm.xo]
exit
