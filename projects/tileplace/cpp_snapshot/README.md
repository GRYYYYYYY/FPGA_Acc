# C++ search snapshot migration

This independent directory preserves the Python files bound by completed
experiment protocols. It implements immutable sparse pressure prefixes,
HPWL/criticality/routed-feedback/congestion cost pairs, and placement/feedback
transactions with cache invalidation and complete rejection rollback.

Build and verify:

```sh
cmake -S projects/tileplace/cpp_snapshot -B /tmp/tileplace-snapshot-build
cmake --build /tmp/tileplace-snapshot-build -j 4
ctest --test-dir /tmp/tileplace-snapshot-build --output-on-failure
```

Differential tests compare 2,003 pressure queries and 500 cost pairs against
the current Python reference. State tests cover feedback replacement followed
by rejection, failed refresh, acceptance, nested transaction rejection,
retained snapshot lifetime and prefix overflow. Address/undefined-behavior
sanitizers pass with leak scanning disabled because this environment prevents
LeakSanitizer from reading process tasks.

Positions retain x/y/subtile/layer. Placement helpers validate site type,
occupancy, region unions and partial fixed constraints, translate macro units
in all four dimensions, and order candidate roots using Python page-floor and
tie-breaking rules. Placement constraint checks pass in the independent CTest
suite. The constrained SearchState constructor validates the initial placement;
every subsequent begin validates the complete candidate before modifying state.
Macro offsets relative to a reference placement are preserved in all four
dimensions. Failed candidates leave placement, feedback and cached costs intact.
The unconstrained constructor remains available for isolated cost/state tests.

This is an intermediate CPU implementation. Native closure orchestration and
feedback refresh remain to be integrated. Cost pairs currently recompute
touched nets; no speedup or complete-search equivalence is claimed.

`compare_proposals.py` serializes real Python contract state to `proposal_query`
and compares complete candidate identities and integer scores. The first real
check uses the archived diffeq final placement, without pressure or routed
feedback: 20 units and 46 improving candidates match. Receipt:
`diffeq_candidates_2026-09-30.json`, with input/source/binary hashes. This is
not an all-unit, dynamic-feedback or full-trajectory result.

The subsequent baseline-placement check reconstructs 286 pressure edges and
52 timing-feedback edges from archived native outputs. All 202 diffeq units
and 3,476 candidate occurrences match Python identities and scores exactly.
Receipt: `diffeq_all_candidates_feedback_2026-09-30.json`. Feedback refresh,
color selection and multi-round native acceptance are not covered by this check.

`propose_color` implements focus filtering, page parity, best-per-unit selection,
identity deduplication, forbidden identity suppression and conflict selection.
`compare_color_trajectory.py` checks two epochs/four colors against Python with
fixed baseline feedback, applies each selected batch to independent placement
mirrors, and compares every resulting layout. All eight phases and eight selected
transactions match (`diffeq_color_trajectory_2026-09-30.json`). This diagnostic
accepts every improving batch; it does not reproduce native-oracle acceptance.

`run_checked_native.py` integrates C++ selection with the unchanged Python
native host orchestration. It records its own implementation identity including
the adapter, C++ source and binary. The diffeq run completed 16 native closures
and 16 checked color calls (forbidden sets reached 10 identities). Search and
feedback signatures, phase records, transaction records and final placement
match the archived Python pilot exactly. Audit receipt:
`../work/cpp_checked_native_diffeq_2026-09-30/differential_audit.json`.
This verifies C++ candidate selection in native acceptance/rollback/feedback
flow; the host still owns placement state and feedback parsing.

`state_server` keeps C++ placement, feedback indexes, cached net costs and saved
state versions in one process. Its command protocol supports color selection,
candidate apply, feedback replacement, save/restore/drop and layout dumps.
`check_state_server.py` verifies the real diffeq contract against Python across
candidate application, feedback replacement, complete snapshot restoration and
failed illegal application. Receipt: `diffeq_state_server_2026-09-30.json`.
This server diagnostic is not yet connected to native closure orchestration.

`run_persistent_native.py` now connects the server to native orchestration.
Candidate apply, snapshot restoration and feedback refresh update the same
resident C++ process; every resulting layout and color selection is checked
against Python. The diffeq run completed 16 closures and 16 color calls with
exact reference trajectory and final placement correspondence. Receipt:
`../work/cpp_persistent_native_diffeq_2026-09-30_run02/differential_audit.json`.
Implementation `2634f0d4bc3ce0a91c0408bf5fdd8de9612278cb5be4ed35caf642ab087a5e34`
is archived (19 files). The first startup failed because the copied binary
lacked an executable bit; that failed attempt and the permission fix are retained.
The Python reference mirror and host feedback parser remain in the validation
path; this run does not measure an optimized C++ speedup.

Additional fixed-parameter native checks pass for tseng (237 blocks, 16 closures)
and apex2 (173 blocks, 18 closures), with exact search/feedback signatures,
transaction/phase records and final layouts matching their archived references.
Summary: `../work/cpp_persistent_native_coverage_2026-09-30/summary.json`.
Together with diffeq this covers three designs and 50 native closures. These
three contracts have no macros or region constraints, so constraint coverage
still relies on the targeted tests rather than these native runs.

`test_constrained_proposals.py` now supplies 12 synthetic constraint fixtures:
60 complete unit candidate comparisons and 48 color/forbidden-set comparisons
match Python. Fixtures cover actual improving macro swaps, cross-layer/subtile
macro offsets, box and union regions, partial and initial-location fixed blocks,
negative coordinates and sparse net IDs. The full six-test CTest suite passes.
Receipt: `constrained_differential_2026-09-30.json`. These synthetic checks do
not establish native QoR or board performance for constrained designs.

`run_fast_native.py` uses C++ selection and phase statistics without asking
Python to enumerate candidate transactions. Python computes audit deltas only
for selected transactions and continues native orchestration/feedback parsing.
Tests explicitly make Python candidate enumeration fail if called; constrained
selected audits and all phase statistics still match. The diffeq native run
passes all 16 closures and reproduces the complete reference trajectory and final
layout (`../work/cpp_fast_native_diffeq_2026-09-30/differential_audit.json`).
Implementation `98655ecf05b0033e72e35442ec566f911ac1a80c66cfbe1635507b2220aa9869`
is archived. Observed process time is 44.14 s versus 101.92 s for the archived
Python pilot; these runs differ in scheduling/affinity and are not a controlled
speedup measurement. All six CTest groups pass, including the new fast-path test.

Controlled CPU color-selection measurement now pins both host and C++ process
to CPU 31, alternates execution order, and uses one warmup plus five repetitions
per design. Median four-color wall-time ratios are 5.56× (diffeq), 7.29× (tseng)
and 3.38× (apex2), with exact selected audits/statistics throughout. This includes
C++ IPC, selected audit and layout checks at fixed baseline layout/feedback;
initialization, feedback parsing and native VPR are excluded. See `CPU_TIMING.md`
and `color_selection_benchmark_2026-09-30.json`. No end-to-end or FPGA speedup
is established by this measurement.

The no-Python-enumeration path also passes native tseng/apex2 runs (16/18
closures). Combined with diffeq, all three designs and 50 native closures match
their reference trajectories, statistics and final placements. Every adapter
check records `python_full_candidate_enumeration: false`. Summary:
`../work/cpp_fast_native_coverage_2026-09-30/summary.json`. These are equivalence
checks, not controlled end-to-end timing measurements.
