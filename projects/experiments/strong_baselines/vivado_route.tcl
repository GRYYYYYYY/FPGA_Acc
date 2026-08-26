if {$argc != 2} { error "usage: vivado_route.tcl placed.dcp output_dir" }
set input_dcp [file normalize [lindex $argv 0]]
set output_dir [file normalize [lindex $argv 1]]
file mkdir $output_dir
open_checkpoint $input_dcp
set start_ms [clock milliseconds]
route_design
set route_ms [expr {[clock milliseconds] - $start_ms}]
write_checkpoint -force [file join $output_dir routed.dcp]
report_route_status -file [file join $output_dir route_status.rpt]
report_timing_summary -delay_type min_max -max_paths 10 -file [file join $output_dir timing_summary.rpt]
report_utilization -file [file join $output_dir utilization.rpt]
report_power -file [file join $output_dir power.rpt]
set out [open [file join $output_dir vivado_metrics.json] w]
puts $out "{\"route_ms\":$route_ms,\"fully_routed\":[report_route_status -boolean_check ROUTED_FULLY],\"route_errors\":[report_route_status -boolean_check ERRORS_IN_ROUTES]}"
close $out
close_design
