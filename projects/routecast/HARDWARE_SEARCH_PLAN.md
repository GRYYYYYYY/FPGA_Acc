# Prepared CSR search hardware contract

Scope: frozen additive independent SOURCE-to-SINK search over actual RR arcs.
The current STL host consumer is the canonical reference, not the hardware
implementation. Tree RC prefixes, dynamic congestion and epochs need separate
state contracts before being represented by this interface.

Use external memory for CSR and dense node labels. Retain raw node/edge/switch
IDs and disabled costs exactly; do not prune detours, backward arcs, same-tile
transitions or parallel edges. A rank is an address, not a merged resource.
Authenticate the graph/cost context before dispatch. Reject unsupported sizes
before changing externally visible prediction state.

Canonical ordering is (accumulated integer cost, hops, raw-edge-ID sequence,
raw node ID). A predecessor representation must reproduce lexicographic path
comparison, including equal-cost zero-weight cycles. Every committed predecessor
must already be settled. Candidate predecessor changes cannot mutate the path
used by an existing queue label. Prototype this representation against the full
host reference before replacing vectors in hardware.

Use an indexed heap with at most one live entry per physical node and explicit
decrease-key; stale-entry queues otherwise require an unproven larger bound.
All graph indices and original IDs require checked uint64 representation.
Accumulate costs with 128 bits. Disabled UINT64_MAX is not a traversable cost.
Do not saturate overflowing arithmetic into a valid route or silently truncate
path output. Full graph size bounds simple path length; observed path percentiles
do not justify a safe fixed hop limit.

Return distinct statuses: COMPLETE, UNREACHABLE, INVALID_INPUT,
UNSUPPORTED_CONTEXT, FRONTIER_CAPACITY, PATH_CAPACITY, WORK_BUDGET.
UNREACHABLE requires exhausted frontier; budget/capacity exhaustion is unknown,
not evidence of unrouteability. A partial multi-sink query does not commit any
new net occupancy. Preserve the previous accepted net on failure. CPU fallback
must be visible in timing, counters and prediction provenance.

Validation gates:

1. Predecessor/indexed-heap CPU prototype: exact paths and work-independent
   semantic parity on cyclic zero-cost, sparse IDs, parallel edges, disabled
   endpoints and large integer costs; full clma and then Koios replay.
2. Fixed storage implementation: explicit exhaustion and failed-query state
   preservation, no hidden heap allocation; sanitizer host tests.
3. HLS C simulation, synthesis and RTL co-simulation in private directories;
   archive source, tool versions, part, clocks, resource/latency reports and
   terminal statuses. C simulation alone proves no throughput or area claim.
4. Transfer/load/preparation/query/validation/fallback time and measured memory
   included in paired controls. Physical execution requires enumerated hardware.

Measured capacity evidence: experiments/csr_hardware_capacity_2026-10-04.
clma's observed maximum is 15 hops, but its safe simple-path bound is 155,279.
Allocating that entire path for every node would require 192,893,784,960 bytes.
This motivates predecessor storage; it does not establish that canonical tie
comparison is efficient. No HLS performance conclusion is available yet.

2026-10-05 interface evidence: the address-corrected experimental AXI ABI
passed four boundary transactions, and the multisink fixture reports PASS
for five transactions (budget, two capacity failures, complete, unreachable).
The multisink shell exit code was not returned by the original tool handle;
receipt preserves this limitation. Host tests passed 64/64 with sanitizer
coverage of the expanded fixture. Main source now retains C null-pointer
checks only outside synthesis: device address zero is legal. Before asserting
context_verified, the host must authenticate allocated, disjoint device regions
and their capacities as well as graph/cost identity. Experimental metadata
counts use m_axi to avoid conditional ap_vld deadlock. A maintained configurable AXI build interface is now available; fixture
depths are not algorithm limits. Full Koios replay/audit and matched quality/benefit controls remain open.

Configurable frozen builds now use tools/prepare_workspace_direct_hls.py with
--depths (explicit per-port JSON allocations), --testbench and --output (new
directory only). It generates the experimentally validated AXI mapping, keeps
accepted counts on the metadata m_axi bundle, copies maintained source/headers
and records hashes. No search limits are derived from interface depths. The
maintained-source multisink validation passed (exit 0, five RTL transactions) in
experiments/workspace_direct_configurable_hls_2026-10-05.

Koios fullgraph capacity analysis: experiments/koios_direct_capacity_2026-10-05/capacity.json. Max distinct sinks 741, safe per-path edge bound n-1=1,976,811. Current duplicated staging/accepted path representation consumes 21.83 GiB under this conservative allocation; total flat ABI allocation is 22.66 GiB using measured host SearchLabel size 40 bytes. This is not measured RTL storage/device allocation. Small observed hop counts do not establish safe bounds. Investigate shared path representation with unchanged canonical output/atomic publication, or include explicit PATH_CAPACITY fallback and all transfer/validation overhead in benefit measurements.
