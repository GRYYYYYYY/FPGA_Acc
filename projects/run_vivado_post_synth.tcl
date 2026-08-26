if {$argc != 3} {
    puts "usage: vivado -mode batch -source run_vivado_post_synth.tcl -tclargs <project_name> <part> <rtl_or_ip_dir>"
    exit 2
}
set project_name [lindex $argv 0]
set part_name [lindex $argv 1]
set source_dir [file normalize [lindex $argv 2]]
set out_dir [file normalize [file join [pwd] vivado_build $project_name]]
create_project -force $project_name $out_dir -part $part_name
set rtl_files [concat [glob -nocomplain -directory $source_dir *.v] [glob -nocomplain -directory $source_dir *.sv] [glob -nocomplain -directory $source_dir *.vhd] [glob -nocomplain -directory $source_dir *.xci]]
if {[llength $rtl_files] == 0} {
    puts "No RTL/IP files found in $source_dir. Run Vitis HLS export first and pass its generated RTL directory."
    exit 3
}
add_files $rtl_files
update_compile_order -fileset sources_1
synth_design -top $project_name -part $part_name
report_utilization -file [file join $out_dir utilization.rpt]
report_timing_summary -file [file join $out_dir timing_summary.rpt]
write_checkpoint -force [file join $out_dir post_synth.dcp]
exit
