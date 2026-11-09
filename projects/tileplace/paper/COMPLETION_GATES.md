# TilePlace completion and DAC manuscript gates

Updated 2026-10-14. Active objective: complete TilePlace, then turn the verified
results into a DAC submission manuscript. Project completion and manuscript
readiness are both required; neither is established yet. Only TilePlace files
may be changed. The goal does not authorize uploading a submission.

## Implementation acceptance

| Gate | Evidence required | Current status |
|---|---|---|
| Final source identity | One adopted source manifest, deterministic build instructions, and explicit mappings to every verification package | Candidate selection pending; preserve the October 4 verified baseline |
| Full five-transaction RTL | Real process exit 0, C postcheck, cosim PASS, 150 complete typed-port comparisons, unchanged frozen sources | October 4 baseline passes; owners, trial-equal, trial-location-inline, best-dimension-guard, cost-position-compare, selection-member-return, commit-find-return, position-entry-ID, position-condition-return and position-remaining-span simulations running; position-ID-comparison-return co-simulation launched |
| Full four-transaction RTL | Real exit 0, C postcheck, cosim PASS, 120 typed comparisons including external forbidden fallback | October 4 baseline passes; candidate queues await five-transaction terminal |
| Native integration | Same candidate source, all nine cases, 202 native trials, 88 checked color calls, 129 unique reference input identities | October 4 baseline passes; candidate validation tails pending. Trial-location-inline, best-dimension-guard, cost-position-compare, selection-member-return, commit-find-return, position-entry-ID, position-condition-return and position-remaining-span native build/integration tests and 129-file input preflights pass; nine-case executions await RTL |
| Internal routed timing | Same XCU280 part, 4 ns clock read before synthesis, real exit 0, verified output hashes, no internal unconstrained endpoints, setup/hold/pulse pass, all nets routed, no DRC errors or critical warnings | No accepted passing candidate. Best completed physical variant: best-dimension-guard postroute RefinePlacement, WNS -0.047 ns, TNS -3.488 ns, 224 setup failures. Cost-position search routing also failed: WNS -0.267 ns, TNS -180.754 ns, 2,496 setup failures. Selection-member return routing failed: WNS -0.277 ns, TNS -104.519 ns, 1,243 setup failures. Commit-find return routing failed: WNS -0.464 ns, TNS -684.959 ns, 6,226 setup failures. Position-entry-ID routing failed: WNS -0.346 ns, TNS -170.455 ns, 2,067 setup failures. Position-condition-return failed: WNS -0.479 ns, TNS -420.669 ns, 4,513 setup failures. Position-remaining-span failed: WNS -0.388 ns, TNS -88.520 ns, 1,162 setup failures. Position-ID-comparison-return failed: WNS -0.323 ns, TNS -95.798 ns, 1,380 setup failures |
| Adoption and regression | Promote only a candidate satisfying all gates; run integration checks; document source and artifact identities | Pending |

RTL boundary inspection is a prerequisite for the timing experiment, not full
functional validation. Native execution cannot replace RTL proof. Results from
different candidates cannot be combined into one passing implementation.
HLS estimated Fmax is not routed timing. OOC timing excludes platform I/O delay
closure and does not establish board frequency or application throughput.

An unapplied best-dimension-guard adoption preview is saved in
`work/best_dimension_guard_adoption_preflight_2026-10-13`: 520 frozen native
files already match the current project, and 17 mapped kernel headers differ.
The patch passes a read-only application check. It is not an adopted version;
source identities must be rechecked and all acceptance gates must pass first.

The native build now accepts `TILEPLACE_HLS_INCLUDE_DIR` and propagates it to
CTest's compiler calls. Default current-source configure/build/CTest and a
separate trial-location-inline copy using that option both pass without a
compiler wrapper (`work/native_build_integration_preflight_2026-10-13`). All 39
candidate implementation mappings remain unchanged; this is build integration
evidence, not the gated nine-case native cohort or candidate adoption.

`work/roots_shift_end_postroute_explore_2026-10-13` completed an independent
post-route physical optimization from the roots candidate's immutable routed
checkpoint. It retained the 4 ns clock and original result, but failed with
WNS -0.170 ns, TNS -53.134 ns and 896 setup failures. The roots candidate's own
full correctness validation remains pending. Best-dimension-guard post-route
Explore also completed but failed setup timing. Its immutable output checkpoint
fed a completed AggressiveExplore experiment with the same 4 ns clock. That
pass improved WNS to -0.073 ns but still failed setup timing. Its immutable
checkpoint fed an AggressiveFanoutOpt experiment motivated by the final
control path's routing delay and fanout. That pass completed with exit 0,
WNS -0.067 ns, TNS -5.634 ns and 267 setup failures. All 332,923 nets are
routed; hold, pulse-width and DRC error checks pass. The package contains a frozen
copy of the physical-chain auditor with only that directive added to its
allowlist; existing tools remain unchanged. Both auditor versions agree on
the completed parent's results. The parent audit and all new verification
files are bound inputs and must not be overwritten.
`tools/audit_postroute_variant.py` and the frozen fanout extension verify the
physical ancestry back to the original standard OOC run. Both remain bound
evidence and must stay unchanged. The existing correctness chain retains sole
ownership of the five/four/native sequence.

A separate AlternateReplication physical experiment completed from the
completed -0.067 ns fanout checkpoint. Its remaining reported worst paths
have substantial routing delay, and the installed Vivado 2022.2 manual
documents this directive as an alternative critical-cell replication strategy.
The package freezes 12 files and five prerequisite receipts, including the
manual, input checkpoint, exact Tcl flow and a local auditor extension adding
only this directive. Recursive parent verification agrees with the archived
audit. The clock remains 4 ns and routing uses NoTimingRelaxation. Final
independent and watcher audits agree: exit 0, WNS -0.050 ns, TNS -4.143 ns,
251 setup failures, all 332,923 nets routed, no hold or pulse-width failures,
and DRC with 25 warnings, no critical warnings and no errors. Setup timing
still fails. The worst reported paths now include AXI read-buffer BRAM to
commit registers and enumerate-size control. The candidate's five-transaction
RTL chain has independently matched all 30 typed outputs for its first
transaction; the remaining four transactions, actual exit and C postcheck
are still required. No source adoption or additional correctness queue results
from this physical experiment.

An iterative AggressiveExplore experiment completed from the
AlternateReplication checkpoint, whose critical paths differ from those of
the earlier AggressiveExplore input. Its eleven frozen files and four
prerequisite receipts preserve the exact checkpoint, unchanged recursive
auditor, 4 ns clock and NoTimingRelaxation route. This tests a further physical
improvement. The primary and watcher audits agree: actual exit 0, WNS
-0.047 ns, TNS -3.488 ns, 224 setup failures, 332,925 fully routed nets,
no hold or pulse-width failures, and DRC with 25 warnings, no critical
warnings and no errors. Setup timing still fails. The worst reported path
runs from the cost-position FSM to the position-loop start register through
13 logic levels, with 4.028 ns data-path delay and 71.697% routing delay.

A separate critical-pin optimization experiment completed from that
checkpoint. The installed Vivado 2022.2 manual describes moving logical LUT
inputs onto faster physical pins when timing improves. Eleven frozen files
and four prerequisite receipts bind the input, exact `-critical_pin_opt`
command, 4 ns clock and NoTimingRelaxation routing. A local auditor extension
accepts only this additional exact flow; all earlier auditors remain unchanged.
The final primary and watcher audits agree: actual exit 0, WNS -0.047 ns,
TNS -3.488 ns, 224 setup failures, 332,925 fully routed nets, no hold or
pulse-width failures, and DRC with 25 warnings, no critical warnings and no
errors. The physical optimization reported zero optimized cells or nets;
the 20 reported worst paths exactly match the input checkpoint's report.
This experiment provides no timing improvement and creates no additional
RTL queue. Setup closure remains unresolved.

A distinct AddRetime physical experiment completed from the iterative
AggressiveExplore checkpoint. The version-matched Vivado 2022.2 UG904
documents this directive for post-route use, adding forward register retiming
to the default physical optimization flow. Twelve frozen files and seven
prerequisite receipts bind the unchanged logical source, checkpoint, 4 ns
clock, NoTimingRelaxation route, documentation and critical-pin negative
result. The new local auditor only adds the exact AddRetime flow mapping.
Primary and watcher audits agree: actual exit 0, WNS -0.047 ns, TNS -3.488 ns,
224 setup failures, 332,925 fully routed nets, no hold or pulse-width failures,
and DRC with 25 warnings, no critical warnings and no errors. Physical
optimization changed zero cells or nets, and all 20 reported worst paths
exactly match the input report. This provides no timing improvement.

A separate Explore experiment completed using the cost-position candidate's
own routed checkpoint (-0.267 ns WNS), whose worst reported path is selection
control to an AXI address enable with 71.206% routing delay. This checkpoint
has not previously received post-route Explore. The frozen package retains
the same candidate source, XCU280 part, 4 ns clock and NoTimingRelaxation route,
and uses unchanged canonical auditors. Primary and watcher audits agree:
actual exit 0, WNS -0.206 ns, TNS -158.103 ns, 2,378 setup failures,
331,445 fully routed nets, no hold or pulse-width failures, and DRC with
25 warnings, no critical warnings and no errors. Setup still fails.
The worst reported path now runs from top-level FSM control to the
identity-trials AXI write-buffer BRAM, with 92.874% routing delay. A separate
AggressiveExplore pass completed from this checkpoint. Primary and watcher
audits agree: exit 0, WNS -0.196 ns, TNS -154.891 ns, 2,369 setup failures,
331,445 fully routed nets, no hold or pulse-width failures, and DRC with
25 warnings, no critical warnings and no errors. The worst path still feeds
the identity-trials write-buffer BRAM: 94.555% of its delay is routing,
including 2.503 ns on a net with 78 loads. A separate AggressiveFanoutOpt
experiment completed from this checkpoint, preserving the same source and
4 ns constraints. Its local auditor adds only that exact directive to the
accepted flow map; all earlier auditors remain unchanged. Primary and watcher
audits agree: actual exit 0, WNS -0.196 ns, TNS -154.891 ns, 2,369 setup
failures, 331,445 fully routed nets, no hold or pulse-width failures, and DRC
with 25 warnings, no critical warnings and no errors. Physical optimization
changed zero cells/nets, and all 20 reported worst paths match the parent.
This attempt provides no timing improvement. The existing functional queue
retains sole ownership of five/four/native work.

The isolated `position_entry_id_stage_2026-10-13` candidate branches from
best-dimension-guard. A trace through the complete worst routed path confirms
that the caller's state selects the shared position ID, whose comparison feeds
the low/high selection and then the 64-bit loop-condition comparison. The new
candidate captures the exact 32-bit ID at function entry while preserving the
original pipelined binary search and all 64-bit bounds. Only the net-cost
header changes among 44 frozen files. Native five/four fixtures and 16,120
queries against both a linear reference and the parent pass; the query probe
also passes ASan/UBSan with leak detection disabled. Independent HLS synthesis
completed with actual exit 0. The terminal audit verifies 44 frozen files and
232 generated RTL/data files. Both position modules capture the ID in state 2
and start the search in state 3. Raw input ID appears only at the capture;
search, final-ID and applicable move comparisons use the captured register.
Both binary-search pipelines match their parent after explicit identifier
renaming and comment removal, including the full 64-bit bounds. A separate
clocked OOC implementation completed with actual exit 0 at 21:55:37 UTC,
using the same part and 4 ns constraint. Independent primary and watcher
audits agree and verify 236 files, ten prerequisites and seven outputs.
Final WNS is -0.346 ns, TNS -170.455 ns, with 2,067 setup failures. All
332,908 nets are routed; hold and pulse checks pass; DRC has 25 warnings
and no critical warnings or errors. The worst path crosses the selection
member-range comparison and AXI read-buffer control (4.327 ns, 12 levels,
78.737% routing). This is worse than the parent standard WNS -0.153 ns.
Full RTL and native-cohort gates remain pending; timing fails and the
candidate has not been adopted.

Position-entry-ID correctness packages are also frozen: five-transaction
cosimulation launched from the audited synthesis project (277 frozen files),
and four-fixture C simulation/synthesis completed separately with exit 0
(45 files). Its independent audit verifies the external forbidden fallback
C fixture and all 232 generated RTL/data files identical to the candidate
and five-transaction package. All 41 implementation files match the candidate
in both packages. Full four-transaction RTL still awaits the five-transaction
terminal gate under the existing queue owner. The native
tree binds 537 files with 39 exact header mappings; only the net-cost header
differs from its best-dimension-guard parent. Configuration, build and CTest
pass. All nine cohort commands match the original reference configuration,
and the 129-file identity preflight passes with nine cases still pending.
A negative launch without RTL receipts exits 1 before execution. One validation
tail now owns five-RTL completion plus four-synthesis completion, followed by
four RTL, nine native cases and the final input-identity audit. No native cohort
execution or full candidate correctness pass is claimed.

Partial correctness progress is separately archived: the owners-wait
five-transaction package has four completed transactions with 120 matching
whole typed-port comparisons and 281 unchanged frozen files. This is not the
separate four-transaction fixture suite and is not a full five-transaction
pass. Trial-equal-protocol also has four completed transactions with 120
matching whole typed-port comparisons and 283 unchanged frozen files,
verified by `primary_partial_transaction_04_audit.json` in its five-RTL package.
Trial-location-inline now has three completed transactions with 90
matching comparisons; best-dimension-guard also has three completed transactions
with 90 matching comparisons. Each has 277 unchanged frozen files, verified
independently. All four still require the remaining
transactions, real exit status and terminal C postcheck.

The independent `cost_position_compare_stage_2026-10-13` candidate branches
from best-dimension-guard and addresses the completed Explore report's worst
position-search path. Native four/five fixtures and 16,120 linear-reference
position queries pass. HLS completed with exit 0 and 230 frozen RTL files.
RTL inspection did **not** find the intended predicate-only register cut: the
predicate remains bypassed during the bounds update. It did find a real
loop-carried cut in both position instances: 64-bit low/high registers update
in state 75, followed by state 2 testing those registers without a bounds
bypass. This actual structure motivates the separate same-4-ns diagnostic
route. That route completed with exit 0, but its final independent audit finds
WNS -0.267 ns, TNS -180.754 ns and 2,496 setup failures. Hold/pulse checks pass.
The worst path now crosses the member-range validation return into selection
memory-request control; a separate RTL diagnosis records the same-cycle return
bypass. Its own full five/four/native validation chain is queued. The
five-transaction XSim has completed one transaction. Independent
`primary_partial_transaction_01_audit.json` verifies 275 unchanged frozen
files and 30 matching whole typed-port comparisons; the remaining four
transactions, actual exit and terminal C postcheck are pending.
Four-fixture C simulation and synthesis
completed with exit 0, 45 frozen inputs verified, and all 230 generated RTL
files identical to the five-transaction package. The native build and CTest
pass, and the nine-case cohort's 129 unique inputs pass preflight. A negative
gate check rejects native execution while RTL is incomplete. The existing
tail alone owns subsequent four-transaction RTL and native execution.
Best-dimension-guard correctness results cannot be inherited by this changed
source. The stage audit script and receipts are bound to the completed route
and must remain unchanged.

`work/selection_member_return_stage_2026-10-13` independently branches from
the frozen cost-position source. It extracts the selection member-range loop
into a separate helper, disables loop pipelining, and stages the return value
with a fixed protocol boundary. Only the selection header changes. Native
five/four fixtures, 2,197 full-width range checks, 20,000 selection differential
and independent status checks, and ASan/UBSan probes pass. HLS synthesis
completed with exit 0. The independent audit verifies 44 frozen inputs and
230 RTL files: the helper captures its result in state 75 and completes in
state 76, with its return driven solely by that register. Caller state
advance checks completion and result; some memory enables use the registered
result directly. This proves the local cycle boundary, not full functional
behavior. Its same-4-ns route completed with actual exit 0, but failed setup:
WNS -0.277 ns, TNS -104.519 ns and 1,243 failing endpoints. The independent
audit verifies 234 frozen inputs, nine prerequisites and all seven output
hashes; all 332,137 routable nets are routed, hold/pulse checks pass, and DRC
has 25 warnings with no errors or critical warnings. The worst path is now
the commit block-search final ID comparison through its 64-bit sentinel mux
and comparison into failure-result register control. A separate diagnosis
motivated the separately evaluated registered, non-inline `find` return candidate described below. Nine of the reported 20 worst paths instead start
in selection identity validation, so this is not proof of a single bottleneck.
Its own five-transaction XSim reached 1/5 at simulation time 45,350,542,000.
An independent partial audit on October 14 verifies 275 frozen files and
30 complete typed-port comparisons, all equal. Four remaining transactions,
actual exit and C postcheck are pending. Four-fixture C simulation
and synthesis completed with exit 0. An independent audit verifies 45 frozen
inputs, 41 matching implementation files, and all 230 RTL files identical to
the five-transaction package. The sole validation tail waits for full five RTL
before starting four-transaction cosim and native9. Its
native source maps 39 headers to the candidate and preserves 537 frozen files;
configure/build/CTest pass. All nine native commands match the reference
configuration, 129 inputs pass preflight, and missing RTL receipts prevent
native execution. Stage audit receipts and the audit script are now bound
route prerequisites and must not be overwritten.

`work/commit_find_return_stage_2026-10-13` branches from the frozen
selection-member source and changes only the commit header. It disables
inlining of `find` and stages its full 64-bit result across a fixed-protocol
boundary, preserving the lower-bound search and count sentinel. Native
five/four fixtures pass. An independent linear-search and parent comparison
checks 38,803 queries; 20,014 batch checks compare return values, exact status
precedence and guarded position buffers against both the parent and a separate
set-based validation/writeback model. ASan/UBSan also pass with leak detection
disabled. HLS synthesis completed with exit 0. The independent structural
check verifies 44 source files and 231 generated files (228 Verilog files and
three ROM initialization files): state 148 captures the full
64-bit find result and state 149 completes the call. The return mux bypasses
the volatile destination during completion, but both mux inputs are registers;
no raw ID comparison bypasses the cycle boundary. The caller waits for
completion in validation and writeback. The same-4-ns route completed with
exit 0; independent audits agree after verifying 235 frozen files, ten
prerequisite bindings and all seven output hashes. Final WNS is -0.464 ns,
TNS is -684.959 ns, and 6,226 of 556,278 setup endpoints fail. All 331,227
routable nets are fully routed; hold and pulse-width checks pass, and DRC
reports 25 warnings, no critical warnings and no errors. This candidate fails
the timing gate. Its worst reported path runs from the identity trial-count
comparison through AXI read control to a read-address register: 4.444 ns,
ten logic levels and 82.876% routing delay. The reported twenty worst paths
also include identity-to-selection count control, encode-range control and
selected-to-AXI control; this subset does not classify every failing endpoint.
The candidate is retained in the diagnostic table and is not adopted. Its independent
five-transaction RTL package freezes 276 files, while its four-transaction
synthesis package freezes 45; both contain the same 41 implementation files.
The five-transaction XSim reached 1/5 completed at the October 14 02:15:30 UTC
observation. An independent partial audit verifies all 276 frozen files and
30 complete typed-port comparisons with equal outputs. The remaining four
transactions, actual process exit and terminal C postcheck are still pending.
Four-fixture synthesis completed with
exit 0; an independent audit verifies all 45 frozen inputs, the 41 implementation
files, passing C simulation with external-forbidden fallback, and all 231
generated files byte-identical to the five-transaction package. Full four RTL
still waits behind the five-transaction gate. Its native stage maps 39 candidate headers into 537
frozen files, with only the commit header differing from its parent native
stage; configure/build/CTest pass. The nine native commands match the original
reference configuration and 129 frozen inputs pass preflight. A negative launch
check confirms missing RTL receipts prevent native execution. Its seventh
validation tail now owns the sequence from five-transaction RTL and four-fixture
synthesis through four-transaction RTL, native differential checks and final
input identity. Full RTL/native-cohort acceptance remains pending, and the
existing six validation tails keep their current jobs. The stage auditor and receipts are now frozen
prerequisites of the route and must not be overwritten.

The roots page-guard route completed with exit 0 but failed setup timing:
WNS -0.603 ns, TNS -572.762 ns and 4,642 failing endpoints. All 332,753 nets
are routed, hold/pulse checks pass, and DRC has no errors or critical warnings.
The result is retained in the 18-row diagnostic table. Its worst path is a
cost-position binary-search control path, also addressed by the separate
cost-position experiment; the two candidates have different source identities.

The identity member-nonzero route also completed with exit 0 but failed setup:
WNS -1.415 ns, TNS -3398.806 ns and 14,019 failing endpoints. All 332,824 nets
are routed, hold/pulse checks pass, and DRC has no errors or critical warnings.
Its result is retained in the same diagnostic table; it is not adopted.

The existing queues remain the sole owners of their five-to-four-to-native
validation chains. Preserve original failed attempts, observed return codes,
and source bindings. Do not restart a live process based on elapsed time.

## Research and manuscript acceptance

| Deliverable | Required completion evidence | Current gap |
|---|---|---|
| Hardware method and scope | Describe the implemented full-color pipeline, external-word ABI, host/oracle boundary, limits and fallback behavior against the final source | IEEE working draft describes the verified baseline and candidate methodology; final adopted-source bindings pending |
| Traceable results | Generate each reported number from a named sealed experiment; distinguish CPU QoR, native differential checks, RTL coverage and OOC results | Final hardware result absent; retain all failed timing variants |
| Fair evaluation | State configurations, datasets, source identities, failure denominator, paired baselines, ablations and measured runtime boundaries | Preserve the source-sealed 9/13 CPU cohort and its four failures; do not promote the mixed-parser archive into fresh evidence |
| Performance claims | Separate native CPU runtime, simulated cycles, implementation estimates, transfer/oracle costs and physical measurements | No physical U280 execution evidence; speedup, power and energy remain unsupported |
| Manuscript | Consistent abstract, contributions, method, evaluation, limitations, figures, citations and artifact instructions | New IEEE working draft integrates method and audited results; final experimental outcome must determine final claims |
| Submission PDF | Venue-correct template, page budget, anonymous text/metadata, readable figures, resolved citations and reproducible build receipt | IEEE working draft compiles within the provisional page budget; final PDF and venue/year review remain pending |

Current DAC 2027 Research Track rules were checked at the
[official call](https://dac.com/2027/program/research-manuscript-submissions)
on 2026-10-13: IEEE format, up to six body pages and one references-only page,
anonymous manuscript and metadata, approximately 100-word abstract. Abstract
and manuscript deadlines are November 11 and 18, 2026, respectively, at 17:00
US Pacific. These are a planning reference until the target year/track is
confirmed, not a claim that the existing draft is compliant.

## Evidence entry points

Paths below are relative to the TilePlace project root. Consult real terminal
receipts, not this dated status snapshot, before making an acceptance decision.

- `work/full_color_trial_volatile_address_stage_2026-10-04/rtl_attempt_01_terminal_audit.json`
- `work/full_color_optimized_four_rtl_2026-10-04/rtl_attempt_01_terminal_audit.json`
- `work/optimized_native_cohort_2026-10-04/final_audit.json`
- `work/optimized_native_cohort_2026-10-04/input_identity_final_audit.json`
- `work/identity_kind_nonzero_clocked_routed_2026-10-13/independent_routed_audit.json`
- `work/roots_shift_end_protocol_stage_2026-10-13/synthesis_independent_terminal_audit.json`
- `work/roots_shift_end_clocked_routed_2026-10-13/independent_routed_audit.json`
- `work/owners_wait_validation_tail_2026-10-12/state.json`
- `work/trial_equal_protocol_validation_tail_2026-10-12/state.json`
- `work/trial_location_inline_validation_tail_2026-10-13/state.json`
- `work/trial_location_inline_native_stage_2026-10-13/native_preflight_audit.json`
- `work/trial_location_inline_native_cohort_2026-10-13/input_identity_preflight_audit.json`
- `work/best_dimension_guard_validation_tail_2026-10-13/state.json`
- `work/best_dimension_guard_native_stage_2026-10-13/native_preflight_audit.json`
- `work/best_dimension_guard_native_cohort_2026-10-13/input_identity_preflight_audit.json`
- `work/cost_position_compare_stage_2026-10-13/rtl_boundary_audit.json`
- `work/cost_position_compare_stage_2026-10-13/synthesis_independent_terminal_audit.json`
- `work/cost_position_compare_clocked_routed_2026-10-13/session_process_observation.json`
- `work/cost_position_compare_four_rtl_2026-10-13/synthesis_independent_terminal_audit.json`
- `work/cost_position_compare_clocked_routed_2026-10-13/primary_independent_audit.json`
- `work/selection_member_return_diagnosis_2026-10-13/analysis.json`
- `work/selection_member_return_stage_2026-10-13/native_preflight_audit.json`
- `work/selection_member_return_stage_2026-10-13/member_probe_sanitized_audit.json`
- `work/selection_member_return_stage_2026-10-13/synthesis_independent_terminal_audit.json`
- `work/selection_member_return_stage_2026-10-13/rtl_boundary_audit.json`
- `work/selection_member_return_clocked_routed_2026-10-13/detached_launch.json`
- `work/selection_member_return_clocked_routed_2026-10-13/primary_independent_audit.json`
- `work/commit_find_return_diagnosis_2026-10-13/analysis.json`
- `work/selection_member_return_native_stage_2026-10-13/native_preflight_audit.json`
- `work/selection_member_return_native_cohort_2026-10-13/input_identity_preflight_audit.json`
- `work/selection_member_return_validation_tail_2026-10-13/state.json`
- `work/selection_member_return_four_rtl_2026-10-13/synthesis_independent_terminal_audit.json`
- `work/selection_member_return_five_rtl_2026-10-13/primary_partial_transaction_01_audit.json`
- `work/cost_position_compare_validation_tail_2026-10-13/state.json`
- `work/cost_position_compare_native_stage_2026-10-13/native_preflight_audit.json`
- `work/cost_position_compare_native_cohort_2026-10-13/input_identity_preflight_audit.json`
- `work/best_dimension_guard_postroute_fanout_2026-10-13/primary_independent_audit.json`
- `work/identity_member_nonzero_clocked_routed_2026-10-13/primary_independent_audit.json`
- `work/best_dimension_guard_postroute_aggressive_2026-10-13/primary_independent_audit.json`
- `work/roots_page_guard_clocked_routed_2026-10-13/primary_independent_routed_audit.json`
- `experiments/tileplace_new_cohort_2026-09-29/final_audit.json`
- `work/owners_return_reconcile_2026-10-09/NEXT_SESSION_HANDOFF.md`

- `work/commit_find_return_stage_2026-10-13/native_preflight_audit.json`
- `work/commit_find_return_stage_2026-10-13/detached_launch.json`

- `work/commit_find_return_stage_2026-10-13/rtl_boundary_audit.json`
- `work/commit_find_return_stage_2026-10-13/synthesis_independent_terminal_audit.json`
- `work/commit_find_return_clocked_routed_2026-10-13/detached_launch.json`
- `work/commit_find_return_clocked_routed_2026-10-13/primary_independent_audit.json`
- `work/commit_find_return_clocked_routed_2026-10-13/critical_path_observation.json`
- `work/identity_trial_control_diagnosis_2026-10-13/analysis.json`
- `work/commit_find_return_validation_preparation_2026-10-13.json`
- `work/commit_find_return_native_stage_2026-10-13/native_preflight_audit.json`
- `work/commit_find_return_native_cohort_2026-10-13/preparation_audit.json`
- `work/commit_find_return_native_cohort_2026-10-13/input_identity_preflight_audit.json`
- `work/commit_find_return_validation_tail_2026-10-13/state.json`
- `work/commit_find_return_four_rtl_2026-10-13/synthesis_independent_terminal_audit.json`
- `work/commit_find_return_five_rtl_2026-10-13/primary_partial_transaction_01_audit.json`
- `work/best_dimension_guard_postroute_replication_2026-10-13/manifest.json`
- `work/best_dimension_guard_postroute_replication_2026-10-13/timing_basis.json`
- `work/best_dimension_guard_postroute_replication_2026-10-13/detached_launch.json`
- `work/best_dimension_guard_postroute_replication_2026-10-13/primary_independent_audit.json`
- `work/best_dimension_guard_postroute_replication_2026-10-13/critical_path_observation.json`
- `work/best_dimension_guard_five_rtl_2026-10-13/primary_partial_transaction_01_audit.json`
- `work/best_dimension_guard_postroute_refine_2026-10-13/manifest.json`
- `work/best_dimension_guard_postroute_refine_2026-10-13/timing_basis.json`
- `work/best_dimension_guard_postroute_refine_2026-10-13/detached_launch.json`

- `work/best_dimension_guard_postroute_refine_2026-10-13/primary_independent_audit.json`
- `work/best_dimension_guard_postroute_refine_2026-10-13/critical_path_observation.json`
- `work/best_dimension_guard_postroute_pinopt_2026-10-13/manifest.json`
- `work/best_dimension_guard_postroute_pinopt_2026-10-13/timing_basis.json`
- `work/best_dimension_guard_postroute_pinopt_2026-10-13/detached_launch.json`
- `work/best_dimension_guard_postroute_pinopt_2026-10-13/primary_independent_audit.json`
- `work/best_dimension_guard_postroute_pinopt_2026-10-13/critical_path_observation.json`
- `work/best_dimension_guard_postroute_retime_2026-10-13/manifest.json`
- `work/best_dimension_guard_postroute_retime_2026-10-13/timing_basis.json`
- `work/best_dimension_guard_postroute_retime_2026-10-13/retiming_documentation.json`
- `work/best_dimension_guard_postroute_retime_2026-10-13/detached_launch.json`
- `work/best_dimension_guard_postroute_retime_2026-10-13/primary_independent_audit.json`
- `work/best_dimension_guard_postroute_retime_2026-10-13/critical_path_observation.json`
- `work/cost_position_compare_postroute_explore_2026-10-13/manifest.json`
- `work/cost_position_compare_postroute_explore_2026-10-13/detached_launch.json`
- `work/cost_position_compare_postroute_explore_2026-10-13/primary_independent_audit.json`
- `work/cost_position_compare_postroute_explore_2026-10-13/critical_path_observation.json`
- `work/cost_position_compare_postroute_aggressive_2026-10-13/manifest.json`
- `work/cost_position_compare_postroute_aggressive_2026-10-13/detached_launch.json`
- `work/cost_position_compare_postroute_aggressive_2026-10-13/primary_independent_audit.json`
- `work/cost_position_compare_postroute_aggressive_2026-10-13/critical_path_observation.json`
- `work/cost_position_compare_postroute_fanout_2026-10-13/manifest.json`
- `work/cost_position_compare_postroute_fanout_2026-10-13/detached_launch.json`
- `work/cost_position_compare_postroute_fanout_2026-10-13/primary_independent_audit.json`
- `work/cost_position_compare_postroute_fanout_2026-10-13/critical_path_observation.json`
- `work/position_entry_path_diagnosis_2026-10-13/analysis.json`
- `work/position_entry_id_stage_2026-10-13/manifest.json`
- `work/position_entry_id_stage_2026-10-13/native_preflight_audit.json`
- `work/position_entry_id_stage_2026-10-13/detached_launch.json`
- `work/position_entry_id_stage_2026-10-13/rtl_boundary_audit.json`
- `work/position_entry_id_stage_2026-10-13/synthesis_independent_terminal_audit.json`
- `work/position_entry_id_clocked_routed_2026-10-13/manifest.json`
- `work/position_entry_id_clocked_routed_2026-10-13/session_process_observation.json`
- `work/position_entry_id_validation_preparation_2026-10-13.json`
- `work/position_entry_id_native_stage_2026-10-13/native_preflight_audit.json`
- `work/position_entry_id_native_cohort_2026-10-13/preparation_audit.json`
- `work/position_entry_id_native_cohort_2026-10-13/input_identity_preflight_audit.json`
- `work/position_entry_id_validation_tail_2026-10-13/manifest.json`
- `work/position_entry_id_validation_tail_2026-10-13/detached_launch.json`
- `work/position_entry_id_four_rtl_2026-10-13/synthesis_independent_terminal_audit.json`
- `work/owners_wait_five_terminal_recovery_2026-10-12/primary_partial_transaction_04_audit.json`
- `work/trial_location_inline_five_rtl_2026-10-13/primary_partial_transaction_02_audit.json`
- `work/best_dimension_guard_five_rtl_2026-10-13/primary_partial_transaction_02_audit.json`

Terminal position-entry evidence:

- `work/position_entry_id_clocked_routed_2026-10-13/primary_terminal_routed_audit.json`
- `work/position_entry_final_path_diagnosis_2026-10-13/analysis.json`

A separate `position_condition_return_stage_2026-10-13` candidate now branches
from best-dimension-guard. Only the net-cost header changes among 44 frozen
files: the full 64-bit `low < high` condition uses a non-inlined fixed-protocol
return stage. The binary-search updates, exact 32-bit ID and move semantics
are unchanged. Native five/four fixtures, 16,120 linear-reference and parent
differential queries, 20,196 full64 condition cases and null-empty behavior
pass. The probe also passes ASan/UBSan with leak detection disabled. HLS
synthesis completed with actual exit 0 at 22:13:20 UTC. The independent
audit verifies all 44 files and 233 generated RTL/data files. The helper
registers both full64 inputs and then the comparison result; its output
connects only to that result register. Both search loops consume the result
in stage 3 under the fixed-latency CE schedule, with no raw low/high
comparison bypass. The generated helper is pipelined despite the source
pipeline-off directive; the audit describes actual RTL, not pragma intent.
A separate clocked 4 ns OOC run completed with actual exit 0 at 23:42:21 UTC.
The primary and watcher audits agree, verifying 237 frozen files,
11 prerequisites and seven output hashes. Final WNS is -0.479 ns, TNS
-420.669 ns, with 4,513 setup failures among 557,897 endpoints. All
333,607 routable nets are fully routed; hold and pulse checks pass, and
DRC reports 25 warnings with no critical warnings or errors. The worst
path crosses an enumeration comparison and shared AXI read control into
the position-memory read-buffer BRAM enable: 4.111 ns, eight logic levels,
86.088% routing delay. Eight of the reported 20 worst paths still terminate
at position-query register enables. This true condition-register boundary
does not close whole-kernel timing and is worse than the parent's standard
-0.153 ns result. The candidate is not adopted.
Five-fixture cosimulation and four-fixture
C simulation/synthesis launched at 22:15:12 UTC. Four-fixture C simulation
and synthesis subsequently completed with actual exit 0. Its independent
audit verifies 45 frozen files, the external forbidden fallback fixture,
41 matching implementation files and all 233 generated files (230 Verilog
and three data files) identical to the candidate and five-transaction package.
The five RTL package binds all 233 generated files. This is not a full
four-transaction RTL pass; that execution still awaits five-RTL completion. The 537-file native
tree has 39 mapped headers, and configure/build/CTest pass. Nine original
reference-equivalent commands and 129 input identities pass preparation
checks; a launch without RTL receipts is rejected before execution. A single
validation tail owns subsequent four RTL and native9/input-identity work.
Full RTL/native cohort correctness remains unproven; routed timing fails.
The previous eight
correctness queues remain independent.

- `work/position_condition_return_stage_2026-10-13/manifest.json`
- `work/position_condition_return_stage_2026-10-13/native_preflight_audit.json`
- `work/position_condition_return_stage_2026-10-13/detached_launch.json`

- `work/position_condition_return_stage_2026-10-13/rtl_boundary_audit.json`
- `work/position_condition_return_stage_2026-10-13/synthesis_independent_terminal_audit.json`
- `work/position_condition_return_clocked_routed_2026-10-13/manifest.json`
- `work/position_condition_return_clocked_routed_2026-10-13/primary_terminal_routed_audit.json`
- `work/position_condition_final_path_diagnosis_2026-10-13/analysis.json`
- `work/position_condition_return_validation_preparation_2026-10-13.json`
- `work/position_condition_return_native_stage_2026-10-13/native_preflight_audit.json`
- `work/position_condition_return_native_cohort_2026-10-13/preparation_audit.json`
- `work/position_condition_return_validation_tail_2026-10-13/manifest.json`

- `work/position_condition_return_four_rtl_2026-10-13/synthesis_independent_terminal_audit.json`

- `work/trial_location_inline_five_rtl_2026-10-13/primary_partial_transaction_03_audit.json`

A distinct `position_remaining_span_stage_2026-10-13` experiment branches
directly from best-dimension-guard. Only the net-cost header changes among
44 frozen files: binary search represents its interval as a full64 start
and remaining length, replacing the low/high loop comparison with a nonzero
length check. It retains exact32 ID comparisons, the final lookup, unknown-ID
output behavior and last matching move semantics. Native five/four fixtures,
16,120 linear-reference and parent-differential position queries, 53,223
virtual full64 threshold searches, and ASan/UBSan probes pass. The virtual
searches exercise the extracted candidate recurrence with a known threshold
oracle and a uint128 interval invariant; they do not validate huge physical
arrays or replace RTL equivalence. HLS completed with actual exit 0 at
23:59:17 UTC on October 13. Independent terminal and structural audits verify
44 frozen sources and 232 generated files. Both search instances capture the
next full64 low/remaining state in stage 0 and test registered remaining for
zero in stage 1. The old low/high comparator is absent; the exact32 ID
comparison remains. Each loop reports II 73 and depth 73. This confirms the
generated structure, not physical timing or full functional equivalence.

One standard clock-before-synthesis 4 ns routed OOC attempt launched at
00:00:47 UTC on October 14, binding 236 files and 13 prerequisites. It finished
with actual exit 0 at 01:29:26. Independent primary and watcher audits match:
all seven output hashes verify, all 333,014 routable nets are fully routed,
and routing errors are zero. Final WNS is -0.388 ns, TNS -88.520 ns, with
1,162 failing setup endpoints among 557,302. WHS is 0.008 ns; hold and pulse
failures are zero. DRC reports 25 warnings, no critical warnings and no errors.
The candidate fails the 4 ns timing gate and is worse than the parent's
standard -0.153 ns and best physical -0.047 ns results.

The worst reported path runs from an identity comparison register through
control logic and unit-members AXI RREADY to a read-buffer BRAM enable:
4.019 ns data delay, 11 logic levels, 75.867% routing delay. The twenty reported
setup paths comprise six identity-to-unit-members AXI paths, eleven commit
result-reset paths, and three eligible-control paths. No position path appears
in this limited subset; this does not prove closure of every position path.
The final path diagnosis is archived separately. Same-source five-transaction
co-simulation and four-fixture C
simulation/synthesis launched at 00:01:56. The isolated native build and
CTest passed with 537 frozen files and 39 mapped headers; only the net-cost
header differs from the parent native snapshot. Nine reference-equivalent
cohort commands and 129 frozen input identities are prepared, with a negative
check confirming that missing RTL gates prevent cohort launch. One validation
tail launched at 00:02:46 to await full five RTL and four synthesis, then run
full four RTL and native9/identity audits. These final gates remain pending.
No candidate adoption or final timing pass is claimed.

The four-fixture C simulation (including external-forbidden fallback) and HLS
synthesis completed with actual exit 0 at 00:11:10 UTC on October 14. An
independent terminal audit verified 45 frozen files, 41 matching implementation
files, and all 232 generated files (229 Verilog and three ROM initialization
files) identical to both the candidate stage and the five-transaction package.
The five-transaction XSim has started and remains at 0/5 completed; the four
RTL run and native cohort remain pending behind that gate.

- `work/position_remaining_span_stage_2026-10-13/manifest.json`
- `work/position_remaining_span_stage_2026-10-13/native_preflight_audit.json`
- `work/position_remaining_span_stage_2026-10-13/detached_launch.json`
- `work/position_remaining_span_stage_2026-10-13/rtl_structure_audit.json`
- `work/position_remaining_span_stage_2026-10-13/synthesis_independent_terminal_audit.json`
- `work/position_remaining_span_clocked_routed_2026-10-13/manifest.json`
- `work/position_remaining_span_native_stage_2026-10-13/native_preflight_audit.json`
- `work/position_remaining_span_validation_tail_2026-10-13/manifest.json`
- `work/position_remaining_span_four_rtl_2026-10-13/synthesis_independent_terminal_audit.json`

- `work/position_remaining_span_clocked_routed_2026-10-13/primary_terminal_routed_audit.json`
- `work/position_remaining_span_clocked_routed_2026-10-13/independent_routed_audit.json`
- `work/position_remaining_span_final_path_diagnosis_2026-10-14/analysis.json`

A separate `position_id_compare_return_stage_2026-10-14` candidate branches
from best-dimension-guard. Only the net-cost header changes among 44 frozen
files. It moves the exact32 block-ID less-than predicate into a non-inlined
helper with a fixed-protocol registered return, preserving the full64 low/high
search recurrence, final ID check, unknown-ID behavior and last matching move.
The earlier cost-position in-loop staging did not produce its intended
predicate register cut; this experiment uses a separate helper boundary and
does not disable pipelining in the caller loop. Neither the boundary nor a
physical improvement is assumed before generated RTL inspection.

Native five/four fixtures, 16,120 independent linear-reference and parent
comparison queries, 20,144 exact32 predicate cases, null-empty safety, and
ASan/UBSan probes (leak detection disabled) passed. HLS synthesis launched at 01:37:07 UTC on October 14 and completed with
actual exit 0 at 01:45:24. Independent terminal and structural audits verify
44 frozen sources and 233 generated files (230 Verilog and three ROM files).
The helper captures both exact32 IDs and then registers their comparison;
ap_return uses only that register. Both search callers retain full64 bounds
and have no raw ID comparison bypass. The helper is actually pipelined with
latency 2 and II 1 despite the source pipeline-off directive. Caller stages
73/0/1 advance input capture, predicate capture and result consumption; both
search loops report II 74 and depth 75. This proves a local structural cut,
not complete functional equivalence or physical timing.

One standard clock-before-synthesis 4 ns route launched at 01:46:25, binding
237 frozen files and 14 prerequisites. Same-source five co-simulation and
four C simulation/synthesis launched at 01:47:44. Native CMake/build/CTest
passed with 537 frozen files and 39 mapped headers; only net-cost differs
from the native parent. Nine commands match the original reference protocol;
129 frozen input identities verify in preflight, and a negative launch check
rejects missing RTL gates. A single validation tail launched at 01:48:44,
waiting for five RTL and four synthesis before full four RTL and native9.
Four C simulation and synthesis completed with actual exit 0 at 01:57:20 UTC.
The independent terminal audit verifies all 45 frozen files, 41 implementation
files matching the candidate, and all 233 generated files identical to the
candidate and five-transaction package. The external forbidden-fallback C
fixture passed. Full four RTL remains owned by the validation tail and has
not started. Five-transaction XSim is now running, with 0/5 completed at the
01:57:31 observation. Full RTL/native-cohort gates remain unproven; the final routed4ns result below fails.

- `work/position_id_compare_return_stage_2026-10-14/manifest.json`
- `work/position_id_compare_return_stage_2026-10-14/native_preflight_audit.json`
- `work/position_id_compare_return_stage_2026-10-14/detached_launch.json`

- `work/position_id_compare_return_stage_2026-10-14/rtl_boundary_audit.json`
- `work/position_id_compare_return_stage_2026-10-14/synthesis_independent_terminal_audit.json`
- `work/position_id_compare_return_clocked_routed_2026-10-14/manifest.json`
- `work/position_id_compare_return_native_stage_2026-10-14/native_preflight_audit.json`
- `work/position_id_compare_return_validation_tail_2026-10-14/manifest.json`
- `work/position_id_compare_return_four_rtl_2026-10-14/synthesis_independent_terminal_audit.json`


### Position-ID-comparison-return final route (October 14, 03:13 UTC)

Vivado completed with actual exit 0 at 03:13:31 UTC. Primary and watcher
independent audits agree on every stable field: 237 frozen files, 14
prerequisites and seven output hashes verified. Final WNS is -0.323 ns,
TNS -95.798 ns, with 1,380 of 557,938 setup endpoints failing at 4 ns.
All 333,080 nets are routed; hold and pulse failures are zero. DRC reports
25 warnings, zero critical warnings and zero errors. This candidate fails
acceptance and is worse than its parent standard result (-0.153 ns).

The worst path starts at identity v_count bit30 and ends at the commit
comparison register. Data delay is 4.306 ns, of which 3.693 ns (85.763%) is
routing. The comparison-output net alone contributes 1.850 ns with fanout4;
the following ready-control net contributes 0.715 ns with fanout46.
All 20 reported setup paths share this source: 16 end at commit comparison
D pins and four at identity return-register CE pins. This subset does not
prove closure of unreported position-search paths.

Do not adopt this version or launch additional physical variants without a
new, evidence-backed hypothesis. Preserve the existing correctness chain;
this decision does not terminate its processes. At 03:21 UTC all eleven
original candidate XSim processes and validation-tail owners remained live.
The best completed physical result remains -0.047 ns with 224 setup failures.

Evidence:
- `work/position_id_compare_return_clocked_routed_2026-10-14/primary_terminal_routed_audit.json`
- `work/position_id_compare_return_clocked_routed_2026-10-14/independent_routed_audit.json`
- `work/position_id_compare_return_final_path_diagnosis_2026-10-14/analysis.json`
- `work/position_id_compare_return_final_path_diagnosis_2026-10-14/process_reconciliation.json`
