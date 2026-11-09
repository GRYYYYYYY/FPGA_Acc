# Native resume implementation contract

This is an implementation contract, not evidence that resume exists.

Private build: compile changed `route.cpp` and `route_net.cpp` into RouteCast;
replace their members in a private copy of `libvpr.a`, retaining upstream input
hashes. Do not change TilePlace sources or archives. No resume environment must
forward original behavior and reproduce the complete cold control paths.

First validate unchanged placement. Load a canonical route using its own packed
NET identity after the ordinary routing structures are initialized; validate
packing, placement, graph, architecture and endpoint bindings. Bind all seed
files before and after use. A different seed placement is initially rejected.
This first control is a prerequisite, not the final placement-update experiment.

Loading calls `init_route_structs` internally; it must be inserted at a single
nonrecursive point after initial router state allocation. Reconstruct occupancy
from loaded trees and validate exact per-NET node unions before iteration one.
Initialize NET delays and STA from loaded trees rather than lookahead estimates.
Avoid overwriting those delays in ordinary initialization. Existing router
connection bookkeeping and local OPIN reservation must match the loaded state.

Add an explicit resume flag to routing setup; first iteration must not force
all processed trees to rebuild. Low-fanout rebuild and critical reroute policies
must be explicit in receipts. Do not simulate resume by incrementing `itry`:
other first-iteration cost, timing, budgeting and termination policies depend on
that index. Emit counts for loaded, retained, pruned and rebuilt trees and assert
occupancy before/after every replacement; no silently cleared seed.

Placement update then requires an explicit seed-to-target state conversion:
join NETs by stable name and bind pin identities; do not reuse seed numeric NET
indices under new packing. Remove entire endpoint-changed NETs from the seed
before resuming, update terminals to target placement, rebuild occupancy, and
compute initial target timing with missing routes conservatively. The original
`read_route` is not a partial-route repair loader: disabling placement digest
verification is not an implementation of this conversion. Design the partial
state import separately and test failure rollback before enabling new placement.

Required controls: no-resume private binary vs original cold; unchanged-placement
resume with all retained initial paths proven; target-placement resumed route
FULL/STA with canonical zero-fixup path preservation; same-target cold routing
with identical input, seed, width and worker settings. Retention is measured
before and after routing, not inferred from final overlap. Charge mapping,
loading, updates, final exact route and validation to the full workflow.

Failure receipts include the original seed and target identities, all logs,
exit status and retained/removed counts. A failed import must not publish a
partial state. This experiment is serial; concurrency/durable publication and
physical-board performance remain separate requirements.
