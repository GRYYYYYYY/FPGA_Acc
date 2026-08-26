# PersistRoute: Persistent-State Transactional Routing Acceleration for FPGAs

## Abstract draft

Negotiated-congestion FPGA routing repeatedly traverses a large routing-resource
graph while updating occupancy, history cost, route trees, and timing
criticality. Moving individual searches to an accelerator leaves repeated state
transfer and synchronization on the critical path. PersistRoute instead keeps
the production routing state resident in HBM across rip-up-and-reroute
iterations. Four Search compute units speculatively produce versioned candidate
paths using banked MultiQueues, while a deterministic Commit unit validates and
applies transactions in a fixed priority order. A host control layer preserves
PathFinder semantics and periodically invokes VPR/Tatum to refresh
per-connection setup criticality. The complete design implements on an AMD
Alveo U280 at 180 MHz with positive setup and hold slack, and RTL hardware
emulation matches the HBM C-model byte-for-byte on parallel and negotiated-
congestion real-VPR subsets. Ten paired VTR, Titan23, and Koios cases establish
an auditable deterministic multicore VPR baseline. Physical-board runtime and
energy results remain required before this abstract can include an acceleration
claim.

## Contributions

1. A persistent routing state organization that retains graph, occupancy,
   history, versions, queues and route transactions across complete RRR
   iterations in U280 HBM.
2. A two-level execution scheme combining connection-level Search-CU
   parallelism with banked MultiQueue exploration inside each connection.
3. A version-checked, fixed-order Commit protocol that converts overlapping
   speculative searches into deterministic resource and route-tree updates,
   including replay after conflicts.
4. A production data and timing loop from VPR/FPGAIF inputs through the 32-byte
   task ABI, iterative VPR/Tatum per-connection criticality, XRT execution and
   auditable route export.
5. A layered validation methodology spanning unit tests, HLS C/RTL co-
   simulation, full U280 implementation, multi-CU hardware emulation, VPR
   legality/QoR and commercial FPGA route checking.

## Method summary

At the beginning of an epoch, the scheduler orders connections by descending
timing criticality, then frozen priority and connection ID. Search CUs read the
shared RR graph and a versioned state
snapshot but write only private paths and transaction logs. Each log contains
the resources read, the expected versions and the proposed occupancy/route-tree
updates. The Commit CU consumes completed transactions in that deterministic
order. A transaction commits only if its observed
versions still match; otherwise the connection is placed on the replay queue.
After a full routing iteration, overused resources update negotiated congestion
costs. The optional timing oracle overwrites VPR connection delays from current
RR paths, runs Tatum setup analysis on the real packed timing graph, and feeds
quantized criticality back into the next iteration without changing the task
ABI.

## Evaluation protocol

Use the ten-case frozen academic matrix in `EXPERIMENT_PLAN.md`. Both CPU
baselines use the same TBB-enabled VPR executable; only `--num_workers` differs
(1 versus 16 requested, limited by the eight-logical-CPU host). Each pair uses
the same architecture, synthesized netlist, SDC where available, seed, channel
width and router options. A pair is accepted only when both runs pass and their
route hash, wirelength, CPD and routing-iteration count match. Report whole-flow
and routing-stage times separately. The commercial case uses one placed FPGA24
input for PersistRoute, RWRoute, CUFR and Vivado, followed by the official
checker and Vivado legality reports.

## Current results text

The generated baseline table and figure are in `generated/`. They characterize
the CPU reference and should be regenerated rather than transcribed manually.
The complete hardware design contains four Search CUs, one Commit CU and 32 HBM
pseudo-channel master ports. Post-route timing closes at the requested 180 MHz
data clock with setup WNS +0.016 ns, TNS 0, hold WHS +0.006 ns and THS 0. The
post-synthesis dynamic region uses 186,821 LUTs, 276,771 registers, 108 BRAMs
and 52 DSPs; percentages are emitted in `generated/u280_resource_table.tex`.

On a real `diffeq` RR graph, RTL hardware emulation executes four connections
through all four Search CUs in one wave and produces byte-identical paths,
route trees, iteration records, accelerated-iteration records and resource
state relative to the HBM C-model. A second case begins with one overused
resource and reaches zero overuse after rip-up and reroute in the second
iteration, again with byte-identical outputs. Hardware-emulation time is not
reported as accelerator performance.

The VPR/Tatum timing loop completes three analyses for the full `diffeq` CPU
route and twelve for the four-PE HBM C-model route. Both converge legally with
zero overuse; final critical-path delays are 7.164 ns and 7.274 ns,
respectively. This establishes periodic real-timing feedback functionality,
not broad QoR equivalence across the full benchmark matrix.

On `frisc`, the initial fixed-order HBM C-model is 5.73% above VPR CPD.
Base-cost normalization alone reduces the gap to 3.45%. Four timing-aware
reroute rounds with deterministic criticality-first net ordering close legally
at 13.700 ns versus VPR's 13.588 ns (+0.825%). Two runs produce byte-identical
paths, route trees, resources, congestion logs and timing logs. This is a
single-design timing-policy ablation, not a full-matrix QoR claim.

## Limitations and threats to validity

The VMware guest has no physical U280 PCIe device. Consequently, the current
evidence establishes synthesizability, timing closure and RTL functional
equivalence but not board speedup or energy. The edge delay stored in the
production ABI uses a local VPR RC approximation rather than an exact full
route-tree Elmore model. The timing oracle currently supports clustered VPR
routing and rejects flat routing. The commercial FPGA24 input used so far has
no user timing constraints, so its Vivado result proves route legality but not
timing closure. Finally, the academic baseline matrix is deterministic but
does not replace repeated physical-board trials or multi-seed sensitivity.
