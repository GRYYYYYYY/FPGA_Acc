# Native full-design checks, without route_design or implementation changes.
# Usage: vivado ... -tclargs input.dcp new_dir [export_edif|-] [RW_load.tcl]
if {$argc < 2 || $argc > 4} { error "expected input.dcp new_dir optional_export_edif optional_loader" }
set input [file normalize [lindex $argv 0]]
set output [file normalize [lindex $argv 1]]
if {[file exists $output]} { error "refusing existing output directory: $output" }
file mkdir $output
set_param general.maxThreads 8
if {$argc == 4} {
    source [file normalize [lindex $argv 3]]
} else {
    open_checkpoint $input
}
set f [open [file join $output design.txt] w]
puts $f "part=[get_property PART [current_design]]"
puts $f "design=[current_design]"
puts $f "cells=[llength [get_cells -hierarchical]]"
puts $f "nets=[llength [get_nets -hierarchical]]"
puts $f "slrs=[llength [get_slrs]]"
close $f
report_route_status -file [file join $output route_status.rpt]
report_timing_summary -file [file join $output timing_summary.rpt]
report_utilization -file [file join $output utilization.rpt]
report_drc -file [file join $output drc.rpt]
if {$argc >= 3 && [lindex $argv 2] ne "-"} {
    write_edif [file normalize [lindex $argv 2]]
}
close_design
set f [open [file join $output checks_completed.txt] w]
puts $f "Native reports completed; inspect reports for legality and QoR. No rerouting performed."
close $f
