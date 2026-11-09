# Read-only native timing follow-up. No route_design, optimization or writeback.
# input.dcp loader|- nets.tsv targeted_paths.tsv new-output-directory
if {$argc != 5} {error "expected checkpoint loader|- nets.tsv targeted_paths.tsv output"}
lassign $argv input loader names targets output
if {[file exists $output]} {error "output already exists"}
file mkdir $output
set_param general.maxThreads 8
if {$loader eq "-"} {open_checkpoint $input} else {source $loader}
proc field {value} {
    return [string map [list "\\" "\\\\" "\t" "\\t" "\n" "\\n" "\r" "\\r"] $value]
}
proc row {stream args} {
    set values {}; foreach value $args {lappend values [field $value]}
    puts $stream [join $values "\t"]
}
set f [open [file join $output design.txt] w]
puts $f "part=[get_property PART [current_design]]"
puts $f "cells=[llength [get_cells -hierarchical]]"
puts $f "nets=[llength [get_nets -hierarchical]]"
close $f
report_route_status -file [file join $output route_status.rpt]
report_bus_skew -delay_type min_max -no_detailed_paths -sort_by_slack -warn_on_violation -file [file join $output bus_skew_summary.rpt]
report_bus_skew -delay_type min_max -max_paths 1 -input_pins -sort_by_slack -file [file join $output bus_skew_paths.rpt]
report_timing -delay_type min -max_paths 20 -nworst 1 -input_pins -nets -file [file join $output worst_hold.rpt]
report_timing -delay_type max -max_paths 20 -nworst 1 -input_pins -nets -file [file join $output worst_setup.rpt]

set errors 0
set diag [open [file join $output query_status.tsv] w]
row $diag kind id status object_count
set f [open $targets r]
while {[gets $f line] >= 0} {
    if {[llength [split $line "\t"]] != 3} {error "invalid target row"}
    lassign [split $line "\t"] id source destination
    if {![regexp {^[a-z0-9_]+$} $id]} {error "invalid target ID"}
    set src [get_pins -quiet $source];set dst [get_pins -quiet $destination]
    if {[llength $src] != 1 || [llength $dst] != 1 || [get_property NAME $src] ne $source || [get_property NAME $dst] ne $destination} {
        row $diag path $id unresolved "[llength $src],[llength $dst]";incr errors;continue
    }
    foreach kind {min max} {
        set paths [get_timing_paths -from $src -to $dst -delay_type $kind -max_paths 1]
        if {[llength $paths] != 1} {row $diag path "${id}_${kind}" missing [llength $paths];incr errors;continue}
        report_timing -from $src -to $dst -delay_type $kind -max_paths 1 -input_pins -nets -file [file join $output "target_${id}_${kind}.rpt"]
        set props [open [file join $output "target_${id}_${kind}.tsv"] w]
        row $props property value
        foreach prop [lsort [list_property [lindex $paths 0]]] {row $props $prop [get_property $prop [lindex $paths 0]]}
        close $props;row $diag path "${id}_${kind}" resolved 1
    }
}
close $f
set data [open [file join $output net_delays.tsv] w]
row $data net_id net_name mode object_index property value
set f [open $names r]
while {[gets $f line] >= 0} {
    if {[llength [split $line "\t"]] != 2} {error "invalid net row"}
    lassign [split $line "\t"] id name
    set net [get_nets -quiet $name]
    if {[llength $net] != 1 || [get_property NAME $net] ne $name} {row $diag net $id unresolved [llength $net];incr errors;continue}
    foreach mode {total interconnect} {
        if {$mode eq "total"} {set delays [get_net_delays -of_objects $net]} else {set delays [get_net_delays -interconnect_only -of_objects $net]}
        if {[llength $delays] == 0} {row $diag net "${id}_${mode}" empty 0;incr errors;continue}
        set index 0
        foreach delay $delays {
            foreach prop [lsort [list_property $delay]] {row $data $id $name $mode $index $prop [get_property $prop $delay]}
            incr index
        }
        row $diag net "${id}_${mode}" resolved $index
    }
}
close $f;close $data;close $diag
close_design
set f [open [file join $output completed.txt] w]
puts $f "queries_failed=$errors"
puts $f "routes_changed=false"
close $f
if {$errors} {error "native timing queries failed: $errors; partial reports retained"}
