# TilePlace: deterministic routed-oracle transactional FPGA placement refinement

> **2026-09-29 provenance audit:** A full diffeq timing replay does not reproduce
> the archived V4 trajectory. With the same hashed timing report, the current
> port parser yields 52 initial edges instead of 37. Four development summaries
> plus pdc/dsip disagree with the current parser and match a diagnostic
> restricted-port variant. Archived QoR values remain intact, but the
> single-frozen-implementation / outcome-blind held-out claim is **not verified**.
> Numerical gate checks alone do not close this gap. See
> `../experiments/tileplace_v4_timing_parser_audit_2026-09-29.json`.


> `dac/main.tex` is the manuscript source of truth. This supporting draft still
> preserves the frozen ten-case V1 evidence below; V4 adds atomic swaps/chains,
> routed top-path and congestion feedback, native acceptance, exact rollback,
> stable bisection, and an incumbent-specific no-good frontier. The V4 held-out
> aggregate must not be merged with the older ten-case matrix. The frozen V4
> six-case result passes all five preregistered gates: CPD/WL geomeans are
> -5.049%/-0.507%, 3/6 cases strictly improve CPD, and worst WL is +0.270%.

## Abstract draft

TilePlace is a deterministic post-placement refinement method for heterogeneous FPGA designs. It
decomposes the device into colored pages, evaluates local moves using exact touched-net updates, and
commits proposals only when their site and net write sets are disjoint. Placement macros move as atomic
transactions, while native fixed and regional constraints are preserved. A connection-specific timing
model maps routed timing endpoints back to clustered blocks and protects the highest-criticality
connections with an input-relative distance guard. Across ten academic VPR designs spanning the COFFE
22 nm and Titan23 Stratix IV architecture families, refinement changes routed wirelength and critical-path
delay by -0.066% and -0.911% in geometric mean, with worst-case
changes of +0.439% and +0.017%, respectively. A macro-heavy Koios case preserves all 43
placement macros while reducing routed wirelength by 0.124% at unchanged delay. A separately reported
fixed-I/O point preserves all 28 coordinate-fixed clusters but changes WL/CPD by +0.210%/+0.463%.
These are CPU and VPR
results; hardware acceleration is future work. On the original six-case subset with the same packed
netlists and router, VPR's executable
cluster-level analytical placer changes wirelength and delay by +3.711% and +16.103% in geometric mean
relative to conventional VPR placement.

## Method draft

The device is partitioned into 2×2 pages, selected by a 2×2/4×4/8×8 ablation, and assigned four colors. For each movable block or native VPR
macro, TilePlace enumerates compatible sites in the source page and its eight neighbors. A proposal
recomputes only nets incident to the transaction. Snapshot proposals are sorted deterministically and
committed when both their old/new site write sets and touched-net sets are disjoint. This protocol makes
the accepted batch equivalent to a deterministic serial order without splitting macros.

VPR timing is connection-specific, so a net-level maximum criticality multiplied by HPWL loses the sink
identity needed to estimate timing risk. TilePlace maps RR SOURCE/SINK terminals to clustered blocks using
packed-net pin roles, physical tile footprints for multi-height DSP/memory blocks, and RR class stride for
multi-capacity IO subtiles. Its timing objective
is the sum of connection criticality times source-to-sink Manhattan distance. Connections with quantized
criticality at least 60000 may not become longer than in the input placement.

## Evaluation draft

All QoR comparisons start from frozen VPR 9 placements and use the same VTR revision, architecture,
packed netlist, seed, channel width, single-worker router, and analysis flow within each paired comparison.
The ten timing cases contain 280205 connections fully mapped to clustered source/sink endpoints. Of these,
275654 also map to atom
timing pins; 4551 connections (4440 in conv_layer and 111 in Titan23 stereo_vision) are explicitly labeled as lacking such a mapping, assigned zero
timing criticality, and retained in the wire objective. The strategy and parameters were frozen on four designs before spmv,
softmax, attention_layer, Titan23 neuron, and Titan23 stereo_vision were evaluated. CPU repeats are byte-identical and every candidate passes the
contract validator and VPR placement/routing consistency checks. Across all ten cases, the final strategy
improves geometric-mean routed wirelength by 0.066% and CPD by 0.911%. The post-freeze quintet changes these
metrics by +0.015% and -1.797%, respectively; attention_layer alone changes WL/CPD by
-0.331%/-7.069% without increasing its 15 routing iterations. Improvements are not monotonic per design:
the worst routed
wirelength change is +0.439%, which motivates a future congestion-aware objective. A strict per-transaction
HPWL non-increase rule reduces the worst wirelength regression but loses the geometric-mean improvement,
so it is rejected as the default.

Titan23 neuron is the first post-freeze point from a second architecture family. It uses the unchanged
2×2/q60000 policy and frozen SDC/router parameters, preserves 101 native macros (204 members), and maps all
77106 routed connections to both clustered endpoints and atom timing pins. Its routed WL changes from
766630 to 767301 (+0.088%), CPD remains 7.60292 ns, and routing iterations change from 15 to 16; this
non-improving WL result is retained rather than tuned away.

Titan23 stereo_vision is the second post-freeze point from that architecture family and was preregistered
before its exact Titan 2.0 inputs were acquired. The unchanged policy preserves 150 native macros (300
members). All 81610 routed connections map to clustered endpoints; 81499 map to atom timing pins and the
remaining 111 are explicitly retained with zero timing criticality. Routed WL changes from 592827 to
593627 (+0.135%), CPD changes from 7.51746 to 7.51592 ns (-0.020%), and routing iterations decrease from
15 to 14.

The macro-heavy conv_layer design appeared in an earlier 4×4 algorithm probe, so we do not label it as
independent post-freeze validation. We rerun it with the final 2×2/q60000 configuration as a distinct
previously-probed macro-stress cohort. All 43 native macros (86 members) remain intact; routed WL changes
from 232357 to 232069 (-0.124%), CPD remains 5.12784 ns, and routing iterations change from 14 to 15.

Native fixed and regional constraint support is first validated on two official VTR XML cases with 176
constrained clusters. We then preregister apex4 fixed-I/O as a separate constrained post-freeze QoR point,
without adding it to the unconstrained aggregate. All 28 coordinate-fixed I/O and all 2263 mapped timing
connections are preserved, and complete CPU repeats are byte-identical. Native route/analysis changes WL
from 10023 to 10044 (+0.210%), CPD from 5.20192 to 5.22600 ns (+0.463%), and iterations from 19 to 21.
This retained negative point supports constraint compatibility, not constrained-QoR improvement. It uses
the frozen non-Eigen correctness VPR and is distinct from the unconstrained Eigen AP comparison below.

We additionally rebuilt the exact VPR revision with Eigen 3.4.0 and compared two full placement paths
without changing the packed netlist: conventional timing-driven simulated annealing and the official
cluster-level `--enable_analytic_placer true` path followed by quench. The integrated
`--analytical_place` flow is excluded because it couples packing and placement. Conventional placement
reproduces every frozen baseline WL, CPD, and routing-iteration count. The cluster-level analytical path
is legal on all six cases, but changes routed WL/CPD by +3.711%/+16.103% in geometric mean and improves
neither metric on any case. This negative result is consistent with the path's wirelength-oriented
objective and missing timing-weight update; it establishes a reproducible official baseline but is not
a proxy for an external timing-driven placer.

We also pinned and audited the executable sources and command-line flows of DREAMPlaceFPGA and
AMF-Placer. DREAMPlaceFPGA begins from a flat Bookshelf or FPGA Interchange netlist and performs its own
packing and legalization. AMF-Placer consumes primitive, device, and timing data extracted from an
implemented Vivado design and returns placement Tcl to a Vivado backend. Neither flow preserves the
packed netlist, architecture, or router of our ten-case VPR QoR experiment. We therefore classify them as
B1 executable-source candidates rather than reporting an invalid direct comparison. A future external
placer study requires a separately pre-registered Bookshelf/FPGA Interchange/Vivado cohort.

On one pinned Xeon Gold 6530 logical CPU, the earlier guarded Python reference refinement takes 0.545--59.672 s
in median across the six timing cases after three warm-ups and seven measured repetitions. The two
post-freeze cases spmv and softmax take 59.672 s and 21.798 s, with wall-time CVs of 2.8% and 2.2%.
On the four development cases, eliminating cost computations for disabled candidate guards improves
geometric-mean runtime by 1.439× without changing any placement hash. Fork-process proposal evaluation
is exactly result-equivalent to serial execution for
1, 2, 4, and 8 workers on all four cases. However, the largest clma case shows no controlled process-level
speedup because Python snapshot serialization and IPC dominate; we therefore claim deterministic parallel
semantics, not scalable CPU performance.

These timings exclude the V4 routed-oracle search. V4 pays for accepted and rejected native
route/analysis calls and feedback refresh; a closure-count cap is not a wall-time bound.
Controlled repeated V4 end-to-end timings and an equal-time comparison remain unmeasured.

## Limitations draft

The current implementation is a CPU research prototype and the existing HLS kernel does not implement
the full algorithm. The ten-case benchmark count remains small, quality gains are modest, and there is no physical U280
runtime or energy measurement. The current claim is therefore limited to deterministic VPR post-placement
refinement with native legality, same-router QoR evidence, an executable conventional/AP VPR comparison,
and bounded single-core reference runtime. Independent placer sources have been audited but not reproduced
as comparable B0 results, so no superiority over external placers is claimed.
