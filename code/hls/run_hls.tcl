set script_dir [file dirname [file normalize [info script]]]
set project_dir [file join $script_dir build commit_kernel]

open_project -reset $project_dir
set_top commit_kernel
add_files [file join $script_dir src commit_kernel.cpp] -cflags "-I[file join $script_dir include]"
add_files -tb [file join $script_dir tb commit_kernel_tb.cpp] -cflags "-I[file join $script_dir include]"
open_solution -reset solution_u280
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4.0 -name default

csim_design
csynth_design
cosim_design -rtl verilog
export_design -format xo
exit
