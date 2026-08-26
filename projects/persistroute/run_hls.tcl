set d [file dirname [file normalize [info script]]]
set build_dir [file join $d build]
set include_flags "-I[file join $d include]"
file mkdir $build_dir
cd $build_dir
set only ""
if {[info exists ::env(PERSISTROUTE_HLS_ONLY)]} {set only $::env(PERSISTROUTE_HLS_ONLY)}

# Keep every top in an independent project. Vitis HLS retains design and
# testbench files across solutions in one project, which otherwise links
# multiple testbench main() functions and contaminates kernel reports.
if {$only eq "" || $only eq "search_legacy"} {
open_project -reset search_legacy_project
set_top search_kernel
add_files [file join $d src persistroute.cpp] -cflags $include_flags
add_files [file join $d src multiqueue.cpp] -cflags $include_flags
add_files -tb [file join $d tb persistroute_tb.cpp] -cflags $include_flags
open_solution -reset search_u280
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4.0
config_export -format xo
csim_design
csynth_design
cosim_design -rtl verilog
export_design -format xo -output [file join $build_dir search_kernel_legacy.xo]
close_solution
close_project
}

if {$only eq "" || $only eq "search_hbm"} {
open_project -reset search_hbm_project
set_top search_hbm_kernel
add_files [file join $d src search_hbm.cpp] -cflags $include_flags
add_files [file join $d src multiqueue.cpp] -cflags $include_flags
add_files -tb [file join $d tb search_hbm_tb.cpp] -cflags $include_flags
open_solution -reset search_hbm_u280
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4.0
config_export -format xo
csim_design
csynth_design
cosim_design -rtl verilog
export_design -format xo -output [file join $build_dir search_hbm_kernel.xo]
close_solution
close_project
}

if {$only eq "" || $only eq "scheduler"} {
open_project -reset scheduler_project
set_top multi_pe_schedule
add_files [file join $d src multi_pe.cpp] -cflags $include_flags
add_files -tb [file join $d tb multi_pe_tb.cpp] -cflags $include_flags
open_solution -reset scheduler_u280
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4.0
config_export -format xo
csim_design
csynth_design
cosim_design -rtl verilog
export_design -format xo -output [file join $build_dir multi_pe_schedule.xo]
close_solution
close_project
}

if {$only eq "" || $only eq "commit_legacy"} {
open_project -reset commit_legacy_project
set_top commit_kernel
add_files [file join $d src persistroute.cpp] -cflags $include_flags
add_files [file join $d src multiqueue.cpp] -cflags $include_flags
add_files -tb [file join $d tb persistroute_tb.cpp] -cflags $include_flags
open_solution -reset commit_u280
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4.0
config_export -format xo
csim_design
csynth_design
cosim_design -rtl verilog
export_design -format xo -output [file join $build_dir commit_kernel_legacy.xo]
close_solution
close_project
}

if {$only eq "" || $only eq "commit_hbm"} {
open_project -reset commit_hbm_project
set_top commit_hbm_kernel
add_files [file join $d src commit_hbm.cpp] -cflags $include_flags
add_files -tb [file join $d tb commit_hbm_tb.cpp] -cflags $include_flags
open_solution -reset commit_hbm_u280
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4.0
config_export -format xo
csim_design
csynth_design
cosim_design -rtl verilog
export_design -format xo -output [file join $build_dir commit_hbm_kernel.xo]
close_solution
close_project
}
exit
