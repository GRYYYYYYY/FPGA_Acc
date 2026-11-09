# Read-only timing paths through every requested native logical load.
# input.dcp loader|- load-pins.tsv new-output
if {$argc != 4} {error "expected checkpoint loader|- load-pins.tsv output"}
lassign $argv input loader loads output
if {[file exists $output]} {error "output exists"}
file mkdir $output
set_param general.maxThreads 8
if {$loader eq "-"} {open_checkpoint $input} else {source $loader}
proc field {value} {return [string map [list "\\" "\\\\" "\t" "\\t" "\n" "\\n" "\r" "\\r"] $value]}
proc row {stream args} {set values {};foreach value $args {lappend values [field $value]};puts $stream [join $values "\t"]}
proc decode {value} {
    set result ""
    for {set i 0} {$i < [string length $value]} {incr i} {
        set c [string index $value $i]
        if {$c eq "\\"} {
            incr i;set c [string index $value $i]
            switch -- $c {t {set c "\t"} n {set c "\n"} r {set c "\r"} "\\" {} default {error "bad TSV escape"}}
        }
        append result $c
    }
    return $result
}
set status [open [file join $output query_status.tsv] w]
set data [open [file join $output paths.tsv] w]
set bindings [open [file join $output net_bindings.tsv] w]
set segments_out [open [file join $output net_segments.tsv] w]
row $status net_id to_pin kind status object_count
row $data net_id to_pin kind property value
row $bindings net_id to_pin requested_net direct_net segment_count
row $segments_out net_id to_pin segment
set f [open $loads r];gets $f header
if {$header ne "net_id\tnet_name\tto_pin"} {error "bad input header"}
set errors 0;set count 0;set no_paths 0
while {[gets $f line] >= 0} {
    set fields [split $line "\t"];if {[llength $fields] != 3} {error "bad input row"}
    lassign $fields id netname pinname;set netname [decode $netname];set pinname [decode $pinname]
    set pins [get_pins -quiet $pinname];set net [get_nets -quiet $netname]
    if {[llength $pins] != 1 || [get_property NAME $pins] ne $pinname || [llength $net] != 1 || [get_property NAME $net] ne $netname} {
        row $status $id $pinname both unresolved 0;incr errors;continue
    }
    set connected [get_nets -quiet -of_objects $pins]
    set segments [lsort -unique [get_property NAME [get_nets -quiet -segments -of_objects $pins]]]
    if {[llength $connected] != 1 || [lsearch -exact $segments $netname] < 0 || [lsearch -exact $segments [get_property NAME $connected]] < 0} {
        row $status $id $pinname both net_mismatch [llength $connected];incr errors;continue
    }
    row $bindings $id $pinname $netname [get_property NAME $connected] [llength $segments]
    foreach segment $segments {row $segments_out $id $pinname $segment}
    foreach kind {min max} {
        set paths [get_timing_paths -quiet -through $pins -delay_type $kind -max_paths 1]
        if {[llength $paths] == 0} {
            row $status $id $pinname $kind no_reported_path 0;incr no_paths;continue
        }
        if {[llength $paths] != 1} {row $status $id $pinname $kind multiple [llength $paths];incr errors;continue}
        set path [lindex $paths 0]
        row $status $id $pinname $kind resolved 1
        foreach prop {CLASS STARTPOINT_PIN ENDPOINT_PIN DELAY_TYPE CORNER SLACK DATAPATH_DELAY DATAPATH_LOGIC_DELAY DATAPATH_NET_DELAY REQUIREMENT REQUIRED_TIME STARTPOINT_CLOCK ENDPOINT_CLOCK STARTPOINT_CLOCK_DELAY ENDPOINT_CLOCK_DELAY} {
            row $data $id $pinname $kind $prop [get_property $prop $path]
        }
        # Formatting follows the supplied path object; -input_pins is ignored
        # with -of_objects in Vivado 2022.2 and produces a warning.
        report_timing -of_objects $path -file [file join $output "load_${count}_${kind}.rpt"]
    }
    incr count
}
close $f;close $status;close $data;close $bindings;close $segments_out
set f [open [file join $output completed.txt] w]
puts $f "loads=$count";puts $f "queries_failed=$errors";puts $f "no_reported_paths=$no_paths";puts $f "routes_changed=false";close $f
close_design
if {$errors} {error "unresolved native load timing queries: $errors"}
