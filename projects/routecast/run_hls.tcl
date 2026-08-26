set d [file dirname [file normalize [info script]]]
open_project -reset [file join $d build routecast]
set_top routecast_kernel
add_files [file join $d src routecast.cpp] -cflags "-I[file join $d include]"
add_files -tb [file join $d tb routecast_tb.cpp] -cflags "-I[file join $d include]"
open_solution -reset u280
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4.0
csim_design
csynth_design
cosim_design -rtl verilog
export_design -format xo
exit
