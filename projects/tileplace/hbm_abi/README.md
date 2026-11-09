# TilePlace snapshot ABI draft

The first record layout replaces CPU maps and vectors with flat arrays and
record-index ranges. `snapshot_abi.hpp` fixes byte sizes and checks range bounds
without overflow. It is a transport draft, not a completed HLS kernel.

All records use little-endian encoding. IDs are original block/net IDs; type IDs
come from a host-sealed string dictionary. Range offsets/counts are in records
of the named array, not bytes or global HBM addresses. The host validates every
cross-array reference before a snapshot is published. Reserved words must be
zero. The generation is immutable while any search consumer reads it.

The block fixed mask uses bits 0..3 for x/y/subtile/layer; bit 31 indicates a
region restriction, distinguishing unrestricted blocks from an empty region
union. Other bits must be zero. Box restrictions are normalized to region unions.
Macro units retain initial four-dimensional relative offsets. Network members,
connections and unit members use CSR ranges; IDs need not be contiguous.

Prefix lines use axis 0 for horizontal and 1 for vertical. Entries are strictly
sorted coordinates and cumulative pressure *before* that edge. Each line stores
its total separately, so lower_bound beyond the last entry returns total pressure.
A segment is prefix(high)-prefix(low), matching the CPU half-open edge interval.
Pressure base distance remains Manhattan distance times 65536. Routed feedback
connections and focus blocks belong to the same snapshot generation.

Signed normalized deltas must match Python floor division. Products need at least
85 bits for a uint64 delta times Q20; the CPU uses 128-bit intermediates and rejects
int64 score overflow. HLS must preserve this behavior before narrowing. No clamp
or saturation is allowed to silently change proposal ranking.

The initial layout does not prescribe HBM bank mappings, PE counts or maximum
problem size. Next gates are explicit host serialization/deserialization with
malformed-range rejection, round-trip comparison against the sealed CPU snapshot,
and flat-array cost/query equivalence. Bank assignment and HLS resource choices
follow measured access patterns; no hardware performance is claimed here.

`snapshot_codec.py` now explicitly encodes/decodes every record kind. The file
container stores arrays in header order, each header range starting at zero;
nested CSR ranges refer to the corresponding decoded array. Parsing rejects
truncation, trailing bytes, excessive counts, invalid reserved fields, unknown
block references, inconsistent unit membership and malformed prefix indexes.
Round-trip and corruption tests pass. C++ flat-array queries remain pending.

`pack_snapshot.py` now converts a reference engine, including region/fixed
constraints, macro units, sparse net IDs and pressure prefixes, into ABI records.
The real diffeq snapshot has 202 blocks, 1,973 connections, 286 pressure entries
and 52 routed-feedback edges in 132,228 bytes. Exact decode/encode record equality
passes; files and inputs are sealed in
`../work/hbm_snapshot_diffeq_2026-09-30/metadata.json`. Twelve constrained fixture
round trips also reconstruct positions, unit membership, pressure edge weights
and routed feedback exactly.

`FlatPressure` now reads explicit little-endian fields and validates all section
boundaries plus canonical sorted prefix records, then queries continuous prefix
arrays directly. Real diffeq testing matches 3,002 queries against the Python
native-feedback reference, including int32 extremes. An additional 500 constrained
fixture queries and malformed length/identity/count rejection checks pass in
CTest. Receipt: `../work/hbm_snapshot_diffeq_2026-09-30/flat_pressure_audit.json`.
This reader validates pressure data and container bounds; full non-pressure
record semantics and flat-array net costs are still pending. It is a CPU reader,
not a synthesized HLS kernel.

`FlatNetCosts` reads sparse block IDs, placement, CSR members and connections
directly from the binary arrays, validates duplicate IDs, endpoints, reserved net
words and CSR bounds, and computes HPWL/criticality/congestion costs. All 892
diffeq nets (1,973 connections) match Python exactly, with an additional twelve
constrained fixture comparisons and corrupt-reference/range tests passing.
Receipt: `../work/hbm_snapshot_diffeq_2026-09-30/flat_net_audit.json`. Routed
timing deltas, trial updates and complete non-net ABI validation remain pending.

`FlatTrialCosts` adds read-only candidate location overlays and routed-feedback
costs for changed endpoints. Touched net IDs are checked, and evaluating a trial
never replaces the baseline positions. Twelve constrained fixtures with 100
random overlays each match Python before/after tuples; another 200 overlays on
the real diffeq snapshot match exactly (`flat_trial_audit.json` in its snapshot
directory). These are cost-only overlays and need not be legal placements.
Committed layout updates, candidate legality and full ABI semantics remain
separate pending gates.

`FlatPlacement` reconstructs binary sites, region unions, partial fixed fields
and macro reference offsets, validates ownership and the initial placement,
and commits complete candidate layouts only after constraint checks. The real
diffeq snapshot and twelve constrained fixtures load successfully; nonempty
Python-generated legal transactions commit to matching layouts, while invalid
site changes preserve prior positions. Unit-reference corruption is rejected.
Full canonical ABI checks (including all duplicate/unused feedback records) and
integration of committed positions with the flat cost engine remain pending.

`FlatState` now publishes placement constraints and mutable cost-position arrays
as one immutable shared version. A commit validates a copied candidate, updates
the copied cost positions and only then publishes both; snapshots restore both
together. Twelve constrained fixture sequences compare candidate evaluation,
two legal commits, illegal commit rejection and snapshot restoration against
Python. Every subsequent cost tuple matches the current reference layout.
This CPU copy-on-write prototype still awaits full canonical ABI validation and
integration with complete flat-array search/HLS.

`validate_canonical_snapshot` combines net/pressure/layout checks with complete
CSR partition coverage, sorted unique IDs/sites/unit members, sorted unique
routed feedback, in-net connection endpoints, zero unused fixed fields, and
validation of initial as well as current placements. The real diffeq snapshot
and twelve constrained fixtures pass; eight additional malformed snapshots are
rejected. This is a separate strict entry point; existing low-level readers
and the Python codec do not implicitly apply these stricter checks. FlatState
integration and Python strict validation remain the next gate.

Use `strict_snapshot_codec.encode/decode`, `pack_strict_snapshot.py` and
`StrictFlatState` for new snapshot consumers. All invoke canonical validation
before writing, returning parsed data or constructing state. Python and C++
agree on twelve valid fixtures and eight malformed cases. Strict real diffeq
packing preserves the original binary SHA-256; metadata is in
`../work/hbm_strict_snapshot_diffeq_2026-09-30/metadata.json`. Historical
low-level APIs remain available for their archived checks; new flat search
integration must use the strict entries.

`pressure_array_core` removes maps, vectors, exceptions and dynamic allocation
from the pressure query data plane. It consumes validated prefix arrays and
returns explicit range/monotonicity/overflow statuses. AXI interfaces are declared
for the top function. CPU C simulation matches 6,024 constrained queries plus
3,002 native-feedback diffeq queries and checks three fault statuses. Receipt:
`pressure_array_audit_2026-09-30.json`. HLS synthesis, scheduling and resource
results are still unverified; this is one primitive, not the complete search.

## Candidate integration, 2026-09-30

`callback_proposals.hpp` preserves the CPU candidate rules while injecting a cost evaluator. `flat_proposal_query` uses StrictFlatState costs from validated binary CSR data. Differential tests cover 60 unit candidate sets and 48 color selections with forbidden filtering across 12 constrained fixtures, all matching Python identities and scores. This transitional bridge still receives candidate topology and constraints through the text protocol; it is not complete flat search or synthesizable hardware. Next, read candidate metadata directly from the strict snapshot and validate evolving commits/restores.

## Strict snapshot candidate search

`SnapshotSearch` now reads placements, block/site/region constraints, units, fixed units, network members and focus from strict binary metadata. Sparse network IDs are translated back before cost evaluation and proposal publication. Config, guards and forbidden identities remain explicit host inputs. 60 unit candidate sets and 48 forbidden-filtered colors across 12 fixtures match Python identities/scores. Enumeration still uses STL containers; this is CPU integration, not a fully array-only HLS kernel. Search after commit/restore and native feedback replacement remain to be integrated and validated.

## Stateful search differential

`snapshot_search_server` exercises saved versions, legal commits and rejected collisions on one resident search instance. Twelve constrained fixtures match Python through 192 color comparisons before commit, after commit, after rejection and after restore. Reference transitions use the engine apply/restore APIs so cached costs are invalidated. This establishes CPU search/state integration; feedback replacement and native end-to-end execution remain pending.

## Atomic feedback versions

`FeedbackSearch` validates a replacement strict snapshot and constructs its search/cost state before publication. Replacement must match current placement and static block/site/region/network/unit data; pressure prefixes, routed timing edges and focus may change. Saved versions retain the complete search and feedback state; foreign-owner snapshots are rejected. Twelve fixtures cover 12 accepted updates, 36 malformed/topology/placement rejections, 12 restores and 288 Python-equivalent color comparisons. Commit followed by feedback refresh and native VPR adapter integration remain pending. This is CPU version management with STL, not an HLS kernel.

## Commit then refresh integration

Twelve fixtures now also cover legal layout commit before feedback replacement, invalid replacement rejection and complete initial-version restoration (336 matching color comparisons). `native_snapshot_server` adds flushed resident READY/DUMP/QUIT framing; a real 202-block diffeq snapshot passes the interactive protocol smoke check. Native VPR adapter execution has not yet been performed.

## Native snapshot pilot

The strict-snapshot resident adapter completed diffeq native validation: 16 VPR closures and 16 color calls. Independent differential audit confirms complete search/feedback signatures, phases, transactions and final placement match the archived fast C++ pilot. Receipt: `../work/snapshot_native_diffeq_2026-09-30/differential_audit.json`. Python still enumerates candidates for checking; this is semantic integration evidence, not acceleration or hardware performance. Full CTest passed 2/2.

## Extended snapshot native coverage and array roots

Strict snapshot search now matches complete native trajectories on diffeq, tseng and apex2, totaling 50 native closures (16/16/18). See the diffeq audit and `../work/snapshot_native_coverage_2026-09-30/summary.json`. The independent `candidate_root_array` scans validated site records and keeps top K roots in caller storage, matching the existing CPU order for 2000 queries including negative pages and extreme coordinates, plus two invalid-parameter cases. It is not yet integrated into complete candidate search or HLS synthesized.

## Array roots integrated into candidate search

`ArrayRootSearch` uses canonical site arrays and the caller-buffer root selector inside move/swap/macro/chain candidate generation. CPU control still uses STL; root buffers are allocated by the host. 60 unit sets, 48 forbidden-filtered colors and 144 resident adapter calls across constrained fixtures match Python. A dedicated diffeq native pilot is running in `../work/array_root_native_diffeq_2026-09-30`; no native completion or hardware claim yet.

Array-root diffeq native pilot completed and independently audited: 16 closures/16 color calls, exact complete trajectory and final placement. Full CTest passed 3/3. Receipt: `../work/array_root_native_diffeq_2026-09-30/differential_audit.json`.

## Array trial legality

`trial_legality_array` operates on canonical block/site/region arrays, current positions and trial moves without container allocation. It checks target uniqueness, typed site availability, occupant membership in the moved set, region union and fixed coordinates. Sparse block IDs and site coordinates use binary searches; occupancy uses a scan. 6804 queries across 12 constrained fixtures match Python (2085 legal), with 36 unknown/duplicate-ID and invalid-range fault cases. Macro shape and timing guards remain separate. This core is not yet integrated into search or HLS synthesized.

## Array legality integrated

`ArrayLegalSearch` replaces the candidate valid-trial container checker with the array legality core, alongside array root selection. Per-call current-position arrays and per-trial move buffers are constructed by the CPU host. 60 unit candidate sets, 48 forbidden-filtered color sets and 144 resident adapter calls match Python across 12 fixtures. Transaction/macro/guard control remains CPU/STL. The independent diffeq native pilot is running under `../work/array_legal_native_diffeq_2026-09-30`.

Array legality native diffeq pilot completed: 16 closures and 16 candidate calls, independently audited full trajectory and final-placement equivalence. Full CTest passed 3/3. Receipt: `../work/array_legal_native_diffeq_2026-09-30/differential_audit.json`.

## Array macro translation

`macro_translation_array` resolves sparse block IDs in canonical arrays and translates x/y/subtile/layer into caller-provided trial records. A validation pass checks capacity, IDs and all coordinate ranges before any output write. 2000 queries across unit sizes 1–20 match the existing translation reference; 11 faults preserve output buffers, including overflow and underflow in all four dimensions. The targeted CMake/CTest check passes. Inputs require unique validated unit members and non-aliasing output storage. Integration into candidate search and HLS synthesis remain pending.

## Array macro translation integrated

`ArrayMacroSearch` injects the array translation core into direct moves and macro swaps, alongside array root selection and trial legality. Candidate identity/score differential covers 60 unit sets and 48 forbidden colors; resident adapter checks cover 144 calls across 12 fixtures. Both new CMake targets build, and the atomic translation CTest passes. Host trial buffers and transaction/shape/guard control remain STL. Native tseng/apex2 coverage is running in `../work/array_macro_native_coverage_2026-09-30`.

## Array guard core

`guard_array` checks only guards affected by changed endpoints, using strict block lookup and trial overlays without container allocation. 2000 comparisons against an independent full-placement reference pass (376 accepted/1624 rejected), plus two invalid-ID states and exact/one-below thresholds at the maximum int32 two-axis Manhattan distance. Targeted CTest passes. It is not yet integrated into candidate search or HLS synthesized.

Macro integration native coverage completed: tseng 16 and apex2 18 closures, both complete trajectory and final-placement audits pass.

## Array guards integrated

`ArrayGuardSearch` replaces the candidate guard loop with the array core. Nonempty guards remove candidates in all 12 differential fixtures; 60 unit sets and 48 forbidden colors match Python. The resident adapter also passes 144 calls. Both CMake targets build. Host buffers and candidate/transaction control remain STL. Native closure of this guard-integrated version is still pending.

## Array occupancy ownership

`occupancy_array` scans current position records and returns an explicit presence flag plus sparse block/unit IDs, avoiding sentinel ambiguity for UINT32_MAX. 4000 queries match an independent map (2007 hits/1993 misses), plus 20 extreme four-dimensional positions and an empty layout. Targeted CTest passes. It is not yet integrated into candidate search or HLS synthesized. Guard-version native tseng/apex2 coverage is running in `../work/array_guard_native_coverage_2026-09-30`.

## Array occupancy integrated

`ArrayOwnerSearch` assigns canonical unit IDs to block records and injects array occupancy queries into direct-move, swap/macro-swap and chain owner resolution, removing the per-unit occupied-position and owner maps. Sixty unit sets and 48 guarded colors match Python, and the resident adapter passes 144 calls. Host buffers, shape comparisons and transactions still use STL. Native execution of this owner-integrated version remains pending.

## Array macro shape comparison

`macro_shape_array` compares typed four-dimensional relative locations without sorting or allocating. Unique member/position validation is a host prerequisite. 2000 cases (666 equivalent/1334 different), randomized nonroot member orders, two invalid-unit/ID cases and two extreme-coordinate cases pass against sorted reference descriptors. Targeted CTest passes. Search integration and HLS remain pending. Owner-version native tseng validation is running under `../work/array_owner_native_coverage_2026-09-30`; the earlier guard-version apex2 run remains live.

Guard native coverage completed: tseng/apex2 34 closures. Owner-native tseng completed 16 closures, all exact trajectory audits pass.

## Array shape integrated

`ArrayShapeSearch` replaces sorted shape descriptors with array shape equality. Sixty guarded unit sets, 48 guarded colors and 144 resident adapter calls match Python; CMake targets and shape CTest pass. Nine existing successful cohort designs are now running native equivalence under `../work/array_shape_native_coverage_2026-09-30` with original parameters. Bound sources/headers and the server binary must remain unchanged throughout this queued batch. Transaction selection and host buffers remain CPU/STL.
