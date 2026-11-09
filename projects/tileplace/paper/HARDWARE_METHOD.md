# Full-color implementation: source-backed manuscript notes

Checked 2026-10-13 against the October 4 frozen, functionally verified baseline.
These notes prepare the hardware-method section; they do not establish final
candidate adoption, timing closure, or submission readiness. Acceptance gates
are listed in [COMPLETION_GATES.md](COMPLETION_GATES.md).

## Computation boundary

The synthesized `full_color_top` performs one color invocation. Its explicit
array arguments expose placement metadata, positions, objective inputs,
forbidden identities, configuration, scratch space, and results. It does not
invoke VPR or implement the routed-oracle controller. The following operations
execute in order inside this top-level function:

| Operation | Source function | Output consumed by the next operation |
|---|---|---|
| Eligibility | `eligible` | Ordered unit indices for the requested color, with input/range checks |
| Candidate enumeration | `enumerate_color` | Move, swap, macro-swap, chain2 and chain3 descriptors, owner/trial pools and per-unit groups |
| Evaluation | `evaluate_batch` | Integer scores, old/new write-site unions, touched-net ranges and diagnostics |
| External forbidden filtering, when enabled | `filter_external_explicit` | Suppression by complete cross-pool identity, preserving descriptor indices |
| Identity encoding | `encode_rank` / `encode` | Canonical identity records linked to conflict ranges |
| Ranking and selection | `rank_commit` | Per-group best, identity deduplication and deterministic conflict selection |
| Position update and statistics | `commit`, then `color_stats` | Updated positions, selected descriptor indices and per-kind counts |

The stages above are a functional decomposition. They are not evidence of
concurrent streaming stages, achieved initiation intervals, or one candidate
per cycle. The generated design uses sequential control and external-memory
interfaces; physical timing must be measured on the generated RTL.

`evaluate_batch` leaves positions unchanged. Unchanged or rejected candidates
retain their indices with zero score. `commit` first validates the entire
selected batch, including record ranges, known block identifiers and repeated
blocks, before its second pass writes positions. These guarantees assume the
documented canonical input backing and pairwise disjoint scratch buffers.
Scratch data from a failed invocation is discardable. This is algorithmic
batch validation, not a fault-tolerant memory transaction protocol.

## Host and routed-oracle boundary

The native integration invokes the integer color computation through
`host_propose.hpp` on a **private copy of positions**. It decodes the selected
records into the existing proposal protocol. Thus local selection and writes
inside the color computation do not automatically accept a new routed
incumbent. The host search controller retains explicit commit/restore,
native VPR route-and-analysis, trial budgeting, bisection, rejected-identity
management and feedback refresh.

The native capacity-search color branch constructs snapshot words, external
forbidden identities and scratch storage before calling this adapter. The
separate per-unit callback path is not evidence that a full color ran through
the hardware implementation. The existing nine-case audit counts checked
color calls explicitly. CPU execution of shared integer headers and simulation
of the explicit AXI top provide complementary evidence at different scopes.

## Interface and capacity scope

The frozen top declares 51 logical `m_axi` bundles and an AXI-Lite return/control
interface. It reads configuration indices 0 through 35 and writes 14 result
words, including stage/status, enumeration/move counts and five accepted-kind
counts. Buffers use 8-, 32- and 64-bit element types. The complete RTL output
comparison covers all 30 writable ports, including scratch and positions.

Logical bundles are not physical HBM channel assignments. No channel placement,
arbitration bandwidth, platform clock closure or host-device transfer rate is
established by the OOC run. The `depth=4096` declarations used by these fixtures
must not be presented as proof of arbitrary benchmark capacity. Counts,
range checks, scratch capacities, host allocation and eventual platform
mapping require separate treatment in an end-to-end hardware deployment.

## Temporal boundaries and timing experiments

The timing experiments preserve integer widths and selection semantics while
trying explicit register boundaries on measured control paths. A C++ volatile
temporary alone is insufficient evidence: a generated same-state bypass can
retain the original combinational path. Each accepted structural experiment
therefore binds its generated RTL hash to a capture-state/consumer-state audit.

For example, the roots shift-end candidate captures the computed 32-bit reverse
copy bound in state 152 and consumes it in state 153. The subsequent eligible
validation candidate captures the 64-bit block-index return in state 364 and
performs the unknown-block comparison in state 365. These are candidate-specific
scheduling observations, not architectural constants or claims of timing
improvement. Roots has now completed routed implementation with WNS -0.237 ns and 918
setup failures; its timing gate fails. Eligible routed results and both
candidates' full functional acceptance remain pending.

The implementation flow reads a 4 ns clock before synthesis for
`xcu280-fsvh2892-2L-e`, then places, optimizes and routes the design. The final
gate checks setup, hold, pulse width, internal constraints, routing and DRC
against actual terminal receipts and output hashes. No input/output delays are
supplied in this OOC flow. Its result must be labelled internal OOC timing;
HLS Fmax estimates and intermediate placement/router estimates are not final
timing measurements.

## Source and evidence locations

All paths below are relative to the TilePlace project root:

- `work/full_color_trial_volatile_address_stage_2026-10-04/full_kernel.cpp`
- the same package's `wire_control_commit__full_color_words.hpp`,
  `wire_control_commit__evaluate_batch_words.hpp`,
  `wire_control_commit__encode_rank_words.hpp`,
  `wire_control_commit__rank_commit_words.hpp` and `wire_commit__commit_words.hpp`
- `work/optimized_native_stage_2026-10-04/wire_control_commit/host_propose.hpp`
- `work/optimized_native_stage_2026-10-04/wire_full_color_capacity_search/transaction_search.hpp`
- `work/roots_shift_end_protocol_stage_2026-10-13/rtl_boundary_audit.json`
- `work/eligible_validation_index_stage_2026-10-13/rtl_boundary_audit.json`

`work/dac_completion_2026-10-13/hardware_scope_audit.json` records the inspected
source hashes and interface counts. The final manuscript must update these
bindings to the adopted candidate and keep CPU QoR, native equivalence, RTL
coverage, internal OOC timing and physical measurements distinct.
