# Generate configuration artifacts from the already implemented checkpoint.
# No placement, routing, constraint/property override or device programming.
if {$argc != 3} {error "expected input.dcp loader|- new-output-directory"}
lassign $argv input loader output
if {[file exists $output]} {error "output already exists"}
file mkdir $output
set_param general.maxThreads 8
if {$loader eq "-"} {open_checkpoint $input} else {source $loader}
set f [open [file join $output design.txt] w]
puts $f "part=[get_property PART [current_design]]"
puts $f "design=[current_design]"
puts $f "cells=[llength [get_cells -hierarchical]]"
puts $f "nets=[llength [get_nets -hierarchical]]"
close $f
report_route_status -file [file join $output before_route_status.rpt]
set deck [get_drc_ruledecks bitstream_checks]
if {[llength $deck] != 1} {error "missing bitstream DRC rule deck"}
set checks [get_drc_checks -of_objects $deck]
set named_checks [get_drc_checks -ruledecks bitstream_checks]
set names [lsort [get_property NAME $checks]]
if {![llength $checks] || [llength [lsort -unique $names]] != [llength $checks]} {
    error "empty or duplicate bitstream DRC rule enumeration"
}
if {$names ne [lsort [get_property NAME $named_checks]]} {error "DRC enumeration APIs disagree"}
if {![get_property IS_FACTORY_RULE_DECK $deck]} {error "expected factory bitstream rule deck"}
# In this installed Vivado, SIZE=6085 but both documented enumeration APIs
# return 6053 checks even without a loaded design. Preserve both facts; invoke
# the factory deck itself below, rather than selecting our enumerated list.
set f [open [file join $output drc_ruledeck.txt] w]
puts $f "name=[get_property NAME $deck]"
puts $f "factory=[get_property IS_FACTORY_RULE_DECK $deck]"
puts $f "declared_size=[get_property SIZE $deck]"
puts $f "enumerated_checks=[llength $checks]"
puts $f "enumeration_apis_equal=true"
close $f
set f [open [file join $output drc_checks.tsv] w]
puts $f "check\tenabled\tseverity"
foreach check $checks {
    puts $f "[get_property NAME $check]\t[get_property IS_ENABLED $check]\t[get_property SEVERITY $check]"
}
close $f
report_drc -ruledeck bitstream_checks -file [file join $output bitstream_drc.rpt]
write_bitstream [file join $output candidate.bit]
if {![file exists [file join $output candidate.bit]] || [file size [file join $output candidate.bit]] == 0} {
    error "write_bitstream did not produce the requested bitstream"
}
report_route_status -file [file join $output after_route_status.rpt]
set f [open [file join $output bitstreams.tsv] w]
puts $f "file\tbytes"
foreach path [lsort [glob -directory $output *.bit]] {
    puts $f "[file tail $path]\t[file size $path]"
}
close $f
close_design
set f [open [file join $output completed.txt] w]
puts $f "write_bitstream_completed=true"
puts $f "route_design_invoked=false"
puts $f "device_programmed=false"
close $f
