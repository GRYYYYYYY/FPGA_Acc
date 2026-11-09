# Read-only post-route evidence. This never changes the implementation.
if {$argc != 2} {error "usage: CHECKPOINT OUTPUT_DIRECTORY"}
set checkpoint [lindex $argv 0]
set output [lindex $argv 1]
file mkdir $output
open_checkpoint $checkpoint
set part [get_property PART [current_design]]
if {![string match "xcu280-*" $part]} {error "unexpected device: $part"}
report_timing_summary -delay_type min_max -check_timing_verbose -report_unconstrained -max_paths 20 -file $output/timing_summary.rpt
report_utilization -file $output/utilization.rpt
report_utilization -hierarchical -hierarchical_depth 8 -file $output/utilization_hierarchy.rpt
report_utilization -slr -file $output/utilization_slr.rpt
report_route_status -file $output/route_status.rpt
report_drc -file $output/drc.rpt
check_timing -verbose -file $output/check_timing.rpt
set metrics [open $output/metrics.tsv w]
puts $metrics "part\t$part"
foreach {kind delay} {setup max hold min} {
    set paths [get_timing_paths -delay_type $delay -sort_by slack -max_paths 1 -nworst 1 -no_report_unconstrained]
    puts $metrics "${kind}_path_count\t[llength $paths]"
    if {[llength $paths] == 1} {
        set path [lindex $paths 0]
        puts $metrics "${kind}_worst_slack_ns\t[get_property SLACK $path]"
        puts $metrics "${kind}_startpoint\t[get_property STARTPOINT_PIN $path]"
        puts $metrics "${kind}_endpoint\t[get_property ENDPOINT_PIN $path]"
    }
}
close $metrics
set clocks [open $output/clocks.tsv w]
puts $clocks "name\tperiod_ns"
foreach clock [get_clocks] {puts $clocks "[get_property NAME $clock]\t[get_property PERIOD $clock]"}
close $clocks
set kernel_clocks [open $output/kernel_clocks.tsv w]
puts $kernel_clocks "kernel\tcell\tpin\tclock\tperiod_ns"
foreach kernel {dieroute_net_commit_hbm dieroute_native_search_worker_hbm dieroute_native_snapshot_search_hbm} {
    set cells [get_cells -hierarchical -filter "REF_NAME == $kernel"]
    foreach cell $cells {
        foreach pin [get_pins -of_objects $cell -filter {REF_PIN_NAME == ap_clk}] {
            foreach clock [get_clocks -of_objects $pin] {
                puts $kernel_clocks "$kernel\t$cell\t$pin\t[get_property NAME $clock]\t[get_property PERIOD $clock]"
            }
        }
    }
}
close $kernel_clocks
close_design
exit
